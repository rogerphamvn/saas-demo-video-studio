"""Independent shot count on a rendered video: ffmpeg scene-change detection (default threshold 0.30), min 0.2 s

STATUS: TESTED (hub; ran on the 26/09 ProfitBase renders; copied unchanged apart from this docstring)
between cuts. Camera moves / card morphs INSIDE a shot are continuous, so they are mostly not counted - the result is
a FLOOR on the cut count (a ceiling on shot length). Taste target: most shots <= 2.5 s (references/taste-profile.md).

  python scripts/qa/check_shots.py <video.mp4> [threshold] [--out renders/qa]
"""
import pathlib
import re
import subprocess
import sys

args = [a for a in sys.argv[1:] if not a.startswith("--")]
video = pathlib.Path(args[0])
thr = float(args[1]) if len(args) > 1 else 0.30
outd = pathlib.Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else video.parent
err = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-i", str(video), "-vf", f"select='gt(scene,{thr})',showinfo",
                      "-an", "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
ts = [float(x) for x in re.findall(r"pts_time:([0-9.]+)", err)]
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
                           capture_output=True, text=True).stdout)
cuts = []
for t in ts:
    if not cuts or t - cuts[-1] >= 0.2:
        cuts.append(t)
b = [0.0] + cuts + [dur]
shots = [round(y - x, 2) for x, y in zip(b, b[1:])]
long_ = [s for s in shots if s > 2.5]
txt = (f"{video.name}: scene threshold {thr} | cuts {len(cuts)} | shots {len(shots)} | mean {sum(shots) / len(shots):.2f} s | "
       f"max {max(shots):.2f} s | shots > 2.5 s: {len(long_)}\ncuts at: {', '.join(f'{t:.2f}' for t in cuts)}\nshot lengths: {shots}\n")
outd.mkdir(parents=True, exist_ok=True)
(outd / f"shots-{video.stem}.txt").write_text(txt, encoding="utf-8")
print(txt)
