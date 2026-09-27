"""vcheck.py - quick check of ONE raw capture: size, distinct frames/s, keyframe gap, debugger-bar presence, 1 fps sheet.

STATUS: TESTED (ran after every shot on 27/09; generalisation = the bar probe rows derive from --crop-top instead of the
        literal 10/60/72, which are the same numbers for crop_top 70)

  python scripts/capture/vcheck.py footage/R01-boms_t1.mkv [--sheet] [--ss S --t T] [--crop-top 70] [--config project.json]

Prints one JSON line: file, size, fps_container, dur, keyframes, kf_gap_max, unique_frames (mpdecimate), unique_fps,
bar_present "n/m" (1 fps frames where the white debugger bar is at the top: pixel (20,10) and (20,crop_top-10) white,
(20,crop_top+2) not white), sheet path. Frames go to <file dir>/check/<stem>/ (wiped each run).
"""
import argparse
import json
import os
import pathlib
import re
import subprocess
import sys

from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.config import read_config, utf8_stdout  # noqa: E402

utf8_stdout()
ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("file")
ap.add_argument("--sheet", action="store_true")
ap.add_argument("--ss", default=None)
ap.add_argument("--t", default=None)
ap.add_argument("--crop-top", type=int, default=None, help="height of the debugger bar (default capture.crop_top or 70)")
ap.add_argument("--config", default=None)
a = ap.parse_args()
cfg = read_config(a.config or "project.json", required=bool(a.config))
CT = a.crop_top if a.crop_top is not None else int(cfg.get2("capture.crop_top", 70))
f = a.file


def run(c):
    return subprocess.run(c, capture_output=True, text=True, encoding="utf-8", errors="replace")


p = json.loads(run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height,avg_frame_rate:format=duration", "-of", "json", f]).stdout)
st = p["streams"][0]
dur = float(p["format"]["duration"])
out = {"file": os.path.basename(f), "size": f"{st['width']}x{st['height']}", "fps_container": st["avg_frame_rate"], "dur": round(dur, 2)}
# keyframes
k = run(["ffprobe", "-v", "error", "-skip_frame", "nokey", "-select_streams", "v", "-show_entries", "frame=pts_time", "-of", "csv=p=0", f]).stdout.split()
k = [float(x.strip(",")) for x in k if x.strip(",").strip()]
gaps = [round(b - a_, 3) for a_, b in zip(k, k[1:])]
out["keyframes"] = len(k)
out["kf_gap_max"] = max(gaps) if gaps else None
# unique frames (mpdecimate) overall
cmd = ["ffmpeg", "-hide_banner", "-nostats"]
if a.ss:
    cmd += ["-ss", a.ss]
if a.t:
    cmd += ["-t", a.t]
cmd += ["-i", f, "-vf", "mpdecimate=hi=64*4:lo=64*2:frac=0.1", "-f", "null", "-"]
r = run(cmd)
m = re.findall(r"frame=\s*(\d+)", r.stderr)
uniq = int(m[-1]) if m else None
span = float(a.t) if a.t else dur
out["unique_frames"] = uniq
out["unique_fps"] = round(uniq / span, 1) if uniq else None
# 1 fps frames -> bar check + sheet
d = os.path.join(os.path.dirname(f) or ".", "check", os.path.splitext(os.path.basename(f))[0])
os.makedirs(d, exist_ok=True)
for x in os.listdir(d):
    os.remove(os.path.join(d, x))
run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", f, "-vf", "fps=1", os.path.join(d, "f%03d.png")])
fr = sorted(os.listdir(d))
bar = []
for x in fr:
    im = Image.open(os.path.join(d, x)).convert("RGB")
    bar.append(int(im.getpixel((20, 10)) == (255, 255, 255) and im.getpixel((20, CT - 10)) == (255, 255, 255)
                   and im.getpixel((20, CT + 2)) != (255, 255, 255)))
out["bar_present"] = f"{sum(bar)}/{len(bar)}"
if a.sheet and fr:
    w, h = 320, 180
    cols = 6
    rows = (len(fr) + cols - 1) // cols
    sh = Image.new("RGB", (w * cols, h * rows), "black")
    for i, x in enumerate(fr):
        sh.paste(Image.open(os.path.join(d, x)).convert("RGB").resize((w, h)), ((i % cols) * w, (i // cols) * h))
    sp = os.path.join(os.path.dirname(f) or ".", "check", os.path.splitext(os.path.basename(f))[0] + "_sheet.jpg")
    sh.save(sp, quality=70)
    out["sheet"] = sp
print(json.dumps(out, ensure_ascii=False))
