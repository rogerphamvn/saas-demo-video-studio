"""motion.py - per-frame change of a capture (downscaled 384x216 gray): prints each motion segment and the distinct-frame
rate inside it. Used as the E0 motion gate (>= 25 changed frames/s = normal capture; 10-25 = HOLD mode; < 10 = stop).

STATUS: TESTED (27/09 gate + P1/P12 probes; generalisation = --fps / --thr args instead of the literal 60 / 0.05, and the
        loop moved into segments() so e0_gate.py can import it - same arithmetic)

  python scripts/capture/motion.py footage/T.mkv 0 10 [--fps 60] [--thr 0.05]
"""
import argparse
import subprocess

import numpy as np

W, H = 384, 216


def segments(f, ss, t, fps=60.0, thr=0.05):
    """Return [(t_start, t_end, frames, changed, changed_per_s, maxjump)] for each motion segment."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(ss), "-t", str(t), "-i", str(f), "-vf", f"scale={W}:{H},format=gray",
                          "-f", "rawvideo", "-"], capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.int16)
    d = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))
    mv = d > thr
    segs = []
    i = 0
    while i < len(mv):
        if mv[i]:
            j = i
            while j + 1 < len(mv) and (mv[j + 1] or (j + 2 < len(mv) and mv[j + 2]) or (j + 3 < len(mv) and mv[j + 3])):
                j += 1
            segs.append((i, j))
            i = j + 1
        else:
            i += 1
    out = []
    for a, b in segs:
        n = b - a + 1
        u = int(mv[a:b + 1].sum())
        out.append((float(ss) + a / fps, float(ss) + (b + 1) / fps, n, u, u / (n / fps), float(d[a:b + 1].max())))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("ss")
    ap.add_argument("t")
    ap.add_argument("--fps", type=float, default=60.0, help="frame rate of the capture (rec.py writes 60)")
    ap.add_argument("--thr", type=float, default=0.05, help="mean abs gray difference that counts as a change")
    a = ap.parse_args()
    for t0, t1, n, u, rate, mj in segments(a.file, a.ss, a.t, a.fps, a.thr):
        print(f"t={t0:.2f}-{t1:.2f}s frames={n} changed={u} -> {rate:.1f} fps  maxjump={mj:.2f}")
