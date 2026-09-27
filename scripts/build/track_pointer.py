"""Track the recording's own pointer in the raw capture at 30 fps (DENSE track: every frame, not the action log).

Why dense: a virtual cursor tweened between 13 sparse logged points drifted up to 155 px from the real pointer
(ProfitBase test v4). Rest points taken from a 30 fps track land on the real tip.

Per frame (after capture.crop): pointer blob = densest cluster matching pointer_rule; reported tip = top-left-most
pixel of the blob's top rows, bbox, pixel count.

  python scripts/build/track_pointer.py --config project.json --from 31.2 --to 37.4   -> <comp>/data/pointer-track-<a>-<b>.json

STATUS: UNTESTED (hub v2 fallback: only needed when a take has NO capture log; ran on 26/09 ProfitBase v2 footage. Here the
        source is capture.source_capture (a path relative to project.json) and the output goes to <comp>/data. Not re-run.)
"""
import json
import sys
import pathlib

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.sdv_common import load_config, detect_pointer, stream_frames  # noqa: E402


def track(cfg, a, b):
    cap = cfg.get("capture", {})
    w, h = cap.get("w", 1920), cap.get("h", 1080)
    out = []
    for k, f in enumerate(stream_frames(cfg.rel(cfg.need("capture.source_capture")), w, h, vf=cap.get("crop"), ss=a, t=b - a, fps=30)):
        d = detect_pointer(f.astype(np.int16), cfg.get("pointer_rule"))
        out.append({"t": round(a + k / 30, 4), **(d or {"tip": None})})
    return out


if __name__ == "__main__":
    cfg, args = load_config(extra=lambda ap: (ap.add_argument("--from", dest="a", type=float, required=True),
                                              ap.add_argument("--to", dest="b", type=float, required=True)))
    res = track(cfg, args.a, args.b)
    p = cfg.comp("data") / f"pointer-track-{args.a:g}-{args.b:g}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(res), encoding="utf-8")
    print(f"{p.name}: frames {len(res)} with pointer {sum(1 for o in res if o['tip'])}")
