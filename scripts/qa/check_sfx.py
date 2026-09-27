"""Independent SFX audibility check on the stems written by audio/build_mix.py (run it AFTER build_mix.py).

STATUS: SMOKE-TESTED (hub check_sfx.py read the v2 data/timing.json + renders/stems; adapted here to the v3 outputs:
        <comp>/data/sfx-resolved.json + paths.stems_dir. Formula unchanged. Re-run on the synthetic build_mix.py output)

FORMULA (printed in the report - reviewer and builder must measure the same thing, LESSON-07):
  window = [t, t + 0.300 s] per hit in sfx-resolved.json (riser: the LAST 0.300 s of the file as placed)
  level  = RMS dBFS over the window; stereo = sqrt(mean over both channels of x^2); mono = RMS of (L+R)/2
  margin = min(stereo_sfx - stereo_music, mono_sfx - mono_music)          target >= mix.sfx_margin_db (default +6)
Note: build_mix.py itself targets mix.margin_db (+3 in v3) under speech ceilings; this gate reports the stricter +6 view.

  python scripts/qa/check_sfx.py --config project.json [--target 6]   -> <qa_dir>/sfx-margins.tsv, exit 1 if any hit is below
"""
import json
import os
import pathlib
import sys
import wave

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.sdv_common import load_config, decode_stereo, rms_db, out_dir  # noqa: E402

cfg, a = load_config(description=__doc__, extra=lambda ap: ap.add_argument("--target", type=float, default=None))
ROOT, SR = cfg.comp(), 48000
T = json.loads((ROOT / "data" / "sfx-resolved.json").read_text(encoding="utf-8"))
TARGET = a.target if a.target is not None else float(cfg.get2("mix.sfx_margin_db", 6.0))
st = pathlib.Path(os.environ["MIX_STEMS"]) if os.environ.get("MIX_STEMS") else cfg.p("stems_dir")
s, m = decode_stereo(st / "sfx.wav", SR), decode_stereo(st / "music.wav", SR)
W = int(0.3 * SR)
rows = []
for e in T["sfx"]:
    i0 = int(max(e["t"], 0) * SR)
    if "riser" in e["file"]:
        with wave.open(str(ROOT / e["file"])) as w:
            i0 += int(w.getnframes() / w.getframerate() * SR) - W
    stv = rms_db(s[i0:i0 + W]) - rms_db(m[i0:i0 + W])
    mov = rms_db(s[i0:i0 + W].mean(axis=1)) - rms_db(m[i0:i0 + W].mean(axis=1))
    rows.append((min(stv, mov), pathlib.Path(e["file"]).name, e["t"], stv, mov))
bad = [(round(d, 1), f, t) for d, f, t, *_ in rows if d < TARGET]
out = out_dir(cfg) / "sfx-margins.tsv"
out.write_text("t\tfile\tstereo_dB\tmono_dB\tmargin_dB(min)\n" + "\n".join(
    f"{t:.3f}\t{f}\t{x:+.1f}\t{y:+.1f}\t{d:+.1f}" for d, f, t, x, y in sorted(rows, key=lambda r: r[2])) + "\n", encoding="utf-8")
print("formula: window [t, t+0.3 s]; margin = min(stereo, mono) RMS dB of sfx stem minus music stem")
print(f"SFX hits {len(rows)}: min {min(rows)[0]:+.1f} dB  median {float(np.median([r[0] for r in rows])):+.1f} dB  "
      f"below +{TARGET:.0f} dB: {len(bad)} {bad}")
sys.exit(1 if bad else 0)
