"""Loudness + container gate on a DELIVERED file (the renderer re-encodes audio: always measure the final mp4).

STATUS: TESTED (hub; measured the 26/09 ProfitBase FINAL: -14.1 LUFS, -1.8 dBFS, PASS; copied unchanged apart from this docstring)

Pass: integrated -14 +-0.5 LUFS, sample peak <= -1.0 dBFS, audio and video streams the same length (+-0.1 s),
expected size/fps. Prints one line per check and exits 1 on any failure.

  python scripts/qa/check_loudness.py <final.mp4> [--w 1920 --h 1080 --fps 30]
"""
import argparse
import re
import subprocess
import sys

ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("--w", type=int)
ap.add_argument("--h", type=int)
ap.add_argument("--fps", type=float)
ap.add_argument("--lufs", type=float, default=-14.0)
a = ap.parse_args()

o = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-nostats", "-i", a.video, "-af", "ebur128=peak=true", "-f", "null", "-"],
                   capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
o = o[o.rindex("Summary"):]
I = float(re.search(r"I:\s+(-?[\d.]+) LUFS", o).group(1))
peak = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", o).group(1))


def probe(sel, entries):
    return subprocess.run(["ffprobe", "-v", "error", "-select_streams", sel, "-show_entries", entries, "-of", "csv=p=0", a.video],
                          capture_output=True, text=True).stdout.strip().splitlines()[0].split(",")


w, h, rate, vdur = probe("v:0", "stream=width,height,r_frame_rate,duration")
adur = probe("a:0", "stream=duration")[0]
num, den = rate.split("/")
fps = float(num) / float(den)
checks = [
    (f"integrated {I} LUFS (target {a.lufs} +-0.5)", abs(I - a.lufs) <= 0.5),
    (f"sample peak {peak} dBFS (<= -1.0)", peak <= -1.0),
    (f"video {float(vdur):.3f}s vs audio {float(adur):.3f}s (+-0.1)", abs(float(vdur) - float(adur)) <= 0.1),
]
if a.w:
    checks.append((f"size {w}x{h} (want {a.w}x{a.h})", int(w) == a.w and int(h) == a.h))
if a.fps:
    checks.append((f"fps {fps:.3f} (want {a.fps})", abs(fps - a.fps) < 0.01))
for msg, ok in checks:
    print(("PASS " if ok else "FAIL ") + msg)
sys.exit(0 if all(ok for _, ok in checks) else 1)
