"""Contact sheet of a render: 1 frame every --step seconds, time-stamped, tiled --cols wide (several sheets if long).

STATUS: TESTED (hub; ran on the 26/09 ProfitBase renders; copied unchanged apart from this docstring - font = OS candidate list)

Cheapest coarse QA there is - the main session runs it on EVERY render before calling a reviewer: b-roll covering the
film, empty mosaic, 9:16 letterbox/cut text, leftover draft badge are all visible at 1 fps (ProfitBase lesson 9.4).

  python scripts/qa/contact_sheet.py <video.mp4> [--step 1] [--cols 6] [--rows 5] [--width 320] [--out renders/qa]
"""
import argparse
import pathlib
import subprocess

ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("--step", type=float, default=1.0)
ap.add_argument("--cols", type=int, default=6)
ap.add_argument("--rows", type=int, default=5)
ap.add_argument("--width", type=int, default=320)
ap.add_argument("--out", default=None)
a = ap.parse_args()
v = pathlib.Path(a.video)
out = pathlib.Path(a.out) if a.out else v.parent
out.mkdir(parents=True, exist_ok=True)
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(v)],
                           capture_output=True, text=True).stdout)
per = a.cols * a.rows
n_frames = int(dur / a.step) + 1
sheets = []
for s in range(0, n_frames, per):
    t0 = s * a.step
    p = out / f"sheet-{v.stem}-{s // per + 1}.jpg"
    # drawtext needs an explicit fontfile on Windows (no fontconfig: ffmpeg crashes 0xC0000005 without it)
    ff = next((f for f in ("C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                           "/System/Library/Fonts/Supplemental/Arial.ttf") if pathlib.Path(f).exists()), None)
    stamp = (f"drawtext=fontfile='{ff.replace(':', chr(92) + ':')}':text='%{{pts\\:hms}}':x=6:y=6:fontsize=18:fontcolor=white:"
             f"box=1:boxcolor=black@0.6," if ff else "")
    vf = f"fps=1/{a.step},scale={a.width}:-2,{stamp}tile={a.cols}x{a.rows}"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{t0:.3f}", "-copyts", "-i", str(v), "-t", f"{per * a.step:.3f}",
                    "-vf", vf, "-frames:v", "1", "-q:v", "4", str(p)], check=True)
    sheets.append(p)
print(f"{len(sheets)} sheet(s), {n_frames} frames @ {a.step}s:", *[str(s) for s in sheets], sep="\n  ")
