#!/usr/bin/env python3
"""Measure every raw sentence: speech onset/offset (10 ms frames, threshold vo.th_db = -45 dBFS) and the longest silence
inside the sentence. Writes raw_s, on, off, speech_s, max_inner_gap into <vo_dir>/raw/manifest.json (assemble.py uses on/off).

STATUS: TESTED (27/09 ProfitBase; generalised = manifest path from project.json, threshold from vo.th_db)

  python scripts/vo/measure.py --config project.json
"""
import json
import pathlib
import sys
import wave

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
TH_DB = -45.0


def load(f):
    with wave.open(str(f), "rb") as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        return x, w.getframerate()


def env_db(x, sr, win=0.01):
    n = int(sr * win)
    m = len(x) // n
    fr = x[: m * n].reshape(m, n)
    return 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)


def speech_bounds(x, sr, th_db=None):
    th = TH_DB if th_db is None else th_db
    e = env_db(x, sr)
    on = np.where(e > th)[0]
    if not len(on):
        return 0.0, 0.0, 0.0
    s, t = on[0] * 0.01, (on[-1] + 1) * 0.01
    # longest silence inside [s, t]
    inner = e[on[0]: on[-1] + 1] <= th
    best = cur = 0
    for v in inner:
        cur = cur + 1 if v else 0
        best = max(best, cur)
    return s, t, best * 0.01


if __name__ == "__main__":
    from lib.config import load_config  # noqa: E402

    cfg, _ = load_config(description=__doc__)
    th = float(cfg.get2("vo.th_db", TH_DB))
    mp = cfg.p("vo_dir") / "raw" / "manifest.json"
    man = json.loads(mp.read_text(encoding="utf-8"))
    for it in man["items"]:
        x, sr = load(it["file"])
        s, t, gap = speech_bounds(x, sr, th)
        it.update(raw_s=round(len(x) / sr, 3), on=round(s, 3), off=round(t, 3), speech_s=round(t - s, 3), max_inner_gap=round(gap, 2))
        print(f"{it['line']}.{it['idx']} raw {it['raw_s']:5.2f} on {s:4.2f} off {t:5.2f} speech {t-s:5.2f} gap {gap:4.2f} pk {it['peak_abs']}  {it['text_script'][:50]}")
    mp.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
