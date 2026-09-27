#!/usr/bin/env python3
"""Worker VieNeu-TTS: chay BEN TRONG venv cua VieNeu (env VIENEU_PY = <venv>/Scripts/python.exe), KHONG chay bang python he thong.

STATUS: TESTED (hub worker, ran for every VO take of the 26-27/09 ProfitBase case; only this docstring changed)

tts_vn.py --engine vieneu / gen_tts.py / gen_var.py goi file nay qua subprocess:
  <venv>/Scripts/python.exe vieneu_worker.py --in sentences.json --outdir <tmp> [--voice "Ngoc Huyen"]

- sentences.json: list[str] UTF-8 (truyen qua file de tranh loi ma hoa dong lenh Windows voi tieng Viet)
- Load model 1 LAN cho moi cau (load lan dau ~43 s tren CPU cua may dung ca ProfitBase)
- Moi cau -> <outdir>/NNN.wav mono PCM 16-bit, sample rate goc cua VieNeu (48 kHz theo docs/sample.py)
- In ra stdout DUNG 1 dong JSON (ASCII) de ben goi doc: {"rate":..., "files":[...], "load_s":..., "infer_s":[...]}

API dung theo sample.py cua VieNeu-TTS (da chay that 2026-09-25): Vieneu().infer(text, voice=...) -> float32.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf

VIENEU_RATE = 48000  # sample.py + README VieNeu v3 Turbo: output 48 kHz float32


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--voice", default=None)
    a = ap.parse_args()

    sentences = json.loads(Path(a.inp).read_text(encoding="utf-8"))
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    from vieneu import Vieneu  # noqa: E402  (chi co trong venv VieNeu)
    v = Vieneu()
    load_s = time.time() - t0
    rate = int(getattr(v, "sample_rate", 0) or VIENEU_RATE)

    files, infer_s, peaks = [], [], []
    for i, s in enumerate(sentences):
        t1 = time.time()
        audio = v.infer(s, voice=a.voice) if a.voice else v.infer(s)
        infer_s.append(round(time.time() - t1, 2))
        audio = np.asarray(audio, dtype=np.float32).reshape(-1)
        if audio.size == 0:
            print(f"VieNeu tra audio rong cho cau {i + 1}", file=sys.stderr)
            return 3
        peaks.append(round(float(np.max(np.abs(audio))), 3))
        audio = np.clip(audio, -1.0, 1.0)  # float > 1.0 se wrap khi ep int16 -> clip truoc
        f = out / f"{i:03d}.wav"
        sf.write(str(f), audio, rate, subtype="PCM_16")
        files.append(str(f))

    print(json.dumps({"rate": rate, "files": files, "load_s": round(load_s, 1), "infer_s": infer_s,
                      "peak_abs": peaks}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
