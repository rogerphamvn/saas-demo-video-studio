"""flash.py - find the capture times where a 2x2 px sync flash in the bottom-right corner goes dark (browser-side sync mark).

STATUS: TESTED (27/09 sync probes; generalisation = frame size / fps args instead of the literal 1920x1080 @ 60)

  python scripts/capture/flash.py footage/R01-boms_t1.mkv [ss] [t] [--w 1920 --h 1080 --fps 60]

Prints the median brightness and up to 12 times (s) where the corner is >= 40 levels darker than the median.
On 27/09 the flash was NOT visible on one take - the edit then used a DOM event (dialog open) to calibrate instead.
"""
import argparse
import subprocess

import numpy as np

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("file")
ap.add_argument("ss", nargs="?", default="0")
ap.add_argument("t", nargs="?", default="30")
ap.add_argument("--w", type=int, default=1920)
ap.add_argument("--h", type=int, default=1080)
ap.add_argument("--fps", type=float, default=60.0)
a = ap.parse_args()
raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", a.ss, "-t", a.t, "-i", a.file, "-vf", f"crop=4:4:{a.w - 4}:{a.h - 4},format=gray",
                      "-f", "rawvideo", "-"], capture_output=True).stdout
arr = np.frombuffer(raw, np.uint8).reshape(-1, 4, 4)
v = arr[:, 2:, 2:].mean(axis=(1, 2))
base = np.median(v)
hits = [i for i in range(len(v)) if v[i] < base - 40]
print("base", round(float(base), 1), "hits", [round(float(a.ss) + i / a.fps, 3) for i in hits][:12])
