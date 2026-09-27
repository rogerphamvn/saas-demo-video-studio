#!/usr/bin/env python3
"""VO step 1 (grid-first pipeline): synthesise EVERY SENTENCE separately with VieNeu-TTS (model loaded once).

STATUS: SMOKE-TESTED (the 27/09 ProfitBase VO ran this with hard-coded hub paths; generalised = paths/voice from project.json,
        VieNeu python from env VIENEU_PY, line ids via lib.config.norm_line_id, plus a new --fake-tts tone mode.
        Re-run here: --fake-tts, and once with a real local VieNeu venv on a 2-line script - see scripts/README.md)

  python scripts/vo/gen_tts.py --config project.json [--only E05,E08] [--outdir vo/raw] [--fake-tts]

- Sentences = tts_vn.split_sentences() of each `E1|...` line of paths.script_txt (one line -> several sentences on . ! ?).
- The SCRIPT TEXT never changes. Pronunciation fixes go into the TTS INPUT only, via vo.respell_file (default
  <vo_dir>/tts_respell.json) = {"word as written": "respelling"} (27/09: "KPI" -> "cây pi ai" made both ASRs hear "KPI").
- Out: <outdir>/wav/NNN.wav + <outdir>/manifest.json {voice, engine, rate, items:[{line, idx, text_script, text_tts, file,
  infer_s, peak_abs}]}. Next: measure.py -> (asr_check.py / gen_var.py / select_takes.py) -> assemble.py -> align.py.
- --fake-tts: no model, a 220 Hz tone of ~0.28 s/word per sentence (lets measure/assemble/align --asr none run offline).
"""
import json
import os
import pathlib
import re
import subprocess
import sys
import time
import wave

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import tts_vn as g  # noqa: E402
from lib.config import load_config, norm_line_id  # noqa: E402


def fake_tone(text, path, rate=48000):
    n = int(rate * max(0.6, 0.28 * len(text.split())))
    t = np.arange(n) / rate
    x = 0.25 * np.sin(2 * np.pi * 220 * t)
    x[: int(0.1 * rate)] = 0
    x[-int(0.15 * rate):] = 0                      # leading/trailing silence like a real take
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def main():
    cfg, a = load_config(description=__doc__, extra=lambda ap: (
        ap.add_argument("--only", default=""), ap.add_argument("--outdir", default=None),
        ap.add_argument("--vieneu-python", default=os.environ.get("VIENEU_PY", "")),
        ap.add_argument("--fake-tts", action="store_true")))
    only = {norm_line_id(x) for x in a.only.split(",") if x.strip()}
    vo_dir = cfg.p("vo_dir")
    out = pathlib.Path(a.outdir) if a.outdir else vo_dir / "raw"
    voice = cfg.get2("vo.voice")
    rp = cfg.rel(cfg.get2("vo.respell_file", str(vo_dir / "tts_respell.json")))
    respell = json.loads(rp.read_text(encoding="utf-8")) if rp.exists() else {}

    items = []
    for ln in cfg.p("script_txt").read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        lid, text = ln.split("|", 1)
        lid = norm_line_id(lid)
        if only and lid not in only:
            continue
        for k, s in enumerate(g.split_sentences(text)):
            t = s
            for src, dst in respell.items():
                t = re.sub(r"(?<!\w)" + re.escape(src) + r"(?!\w)", dst, t)
            items.append({"line": lid, "idx": k, "text_script": s, "text_tts": t})

    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    if a.fake_tts:
        (out / "wav").mkdir(exist_ok=True)
        files = []
        for i, it in enumerate(items):
            f = out / "wav" / f"{i:03d}.wav"
            fake_tone(it["text_tts"], f)
            files.append(str(f))
        meta = {"rate": 48000, "load_s": 0.0, "files": files, "infer_s": [0.0] * len(items), "peak_abs": [0.25] * len(items)}
    else:
        py = a.vieneu_python
        if not py or not pathlib.Path(py).exists():
            sys.exit(f"VieNeu python not found ('{py}'): set env VIENEU_PY or --vieneu-python (or use --fake-tts)")
        inp = out / "sentences.json"
        inp.write_text(json.dumps([it["text_tts"] for it in items], ensure_ascii=False), encoding="utf-8")
        cmd = [py, str(g.WORKER), "--in", str(inp), "--outdir", str(out / "wav")] + (["--voice", voice] if voice else [])
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        if p.returncode != 0:
            sys.exit(f"worker exit {p.returncode}: {p.stderr[-1500:]}")
        meta = json.loads([ln for ln in p.stdout.splitlines() if ln.startswith("{")][-1])
    for it, f, inf, pk in zip(items, meta["files"], meta["infer_s"], meta["peak_abs"]):
        it.update(file=f, infer_s=inf, peak_abs=pk)
    man = {"voice": voice, "engine": "fake" if a.fake_tts else "vieneu", "rate": meta["rate"], "load_s": meta["load_s"],
           "wall_s": round(time.time() - t0, 1), "respell": respell, "items": items}
    (out / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"OK {len(items)} sentences, rate {meta['rate']}, load {meta['load_s']}s, wall {man['wall_s']}s -> {out / 'manifest.json'}")


if __name__ == "__main__":
    main()
