#!/usr/bin/env python3
"""erase_pointer.py - remove the capture extension's orange pointer dot from cut clips (<comp>/assets/footage/<id>.mp4).
Detector (v2 track_pointer colour rule, pointer = muted orange): R 175-245, G 95-165, B 60-140, R-G 45-110, G-B 5-50;
connected blobs whose bbox is 8-64 px on both sides and near-square (0.5-2.0) = pointer. UI orange larger than 64 px
(chart bars, warning banners) is left alone. Fill: running clean plate (last pixels seen without a pointer at that spot),
fallback = median of a 6 px ring around the box. In place; prints frames-with-pointer before/after.

STATUS: SMOKE-TESTED (27/09 ProfitBase erase_pointer_v3.py; generalised = clip dir, frame size (build.crop) and the colour /
        blob rule (build.erase_rule) from project.json; defaults = the 27/09 literals. Re-run with --probe on a synthetic clip
        (detect + fill ran, re-encode path not run))

  python scripts/build/erase_pointer.py --config project.json e01 e02 ...   (--probe: only count)
"""
import pathlib, subprocess, sys
import numpy as np
from scipy import ndimage

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.config import read_config  # noqa: E402

_argv = sys.argv[1:]
_cfg_path = _argv[_argv.index("--config") + 1] if "--config" in _argv else None
CFG = read_config(_cfg_path or "project.json")
ROOT = CFG.comp()
W, H = [int(v) for v in str(CFG.get2("build.crop", "1920:1010")).split(":")[:2]]
PAD = 8
RULE = {"r": [175, 246], "g": [95, 166], "b": [60, 141], "r_minus_g": [45, 111], "g_minus_b": [5, 51], "blob": [8, 64],
        "aspect": [0.5, 2.0], **CFG.get2("build.erase_rule", {})}   # exclusive colour bounds, as in the 27/09 code


def blobs(f):
    r, g, b = (f[..., i].astype(np.int16) for i in range(3))
    R_ = RULE
    m = ((r > R_["r"][0]) & (r < R_["r"][1]) & (g > R_["g"][0]) & (g < R_["g"][1]) & (b > R_["b"][0]) & (b < R_["b"][1])
         & (r - g > R_["r_minus_g"][0]) & (r - g < R_["r_minus_g"][1]) & (g - b > R_["g_minus_b"][0]) & (g - b < R_["g_minus_b"][1]))
    lab, n = ndimage.label(ndimage.binary_dilation(m, iterations=2))
    out = []
    for sl in ndimage.find_objects(lab):
        if sl is None:
            continue
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        lo_, hi_ = RULE["blob"]
        if lo_ <= h <= hi_ and lo_ <= w <= hi_ and RULE["aspect"][0] <= w / h <= RULE["aspect"][1]:
            out.append((sl[0].start, sl[0].stop, sl[1].start, sl[1].stop))
    return out


def run(cid, probe=False):
    src = ROOT / "assets" / "footage" / f"{cid}.mp4"
    dec = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-i", str(src), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    tmp = src.with_suffix(".tmp.mp4")
    enc = None if probe else subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                               "-r", "30", "-i", "-", "-c:v", "libx264", "-preset", "fast", "-crf", "17", "-g", "15",
                                               "-pix_fmt", "yuv420p", str(tmp)], stdin=subprocess.PIPE)
    plate = None
    seen = np.zeros((H, W), bool)
    n = hit = after = 0
    while True:
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        f = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy()
        n += 1
        bl = blobs(f)
        mask = np.zeros((H, W), bool)
        for y0, y1, x0, x1 in bl:
            mask[max(y0 - PAD, 0):y1 + PAD, max(x0 - PAD, 0):x1 + PAD] = True
        if plate is None:
            plate = f.copy()
        clean = ~mask
        plate[clean] = f[clean]
        seen |= clean
        if bl:
            hit += 1
            for y0, y1, x0, x1 in bl:
                ya, yb, xa, xb = max(y0 - PAD, 0), min(y1 + PAD, H), max(x0 - PAD, 0), min(x1 + PAD, W)
                reg = seen[ya:yb, xa:xb]
                ring = np.concatenate([f[max(ya - 6, 0):ya, xa:xb].reshape(-1, 3), f[yb:yb + 6, xa:xb].reshape(-1, 3),
                                       f[ya:yb, max(xa - 6, 0):xa].reshape(-1, 3), f[ya:yb, xb:xb + 6].reshape(-1, 3)])
                med = np.median(ring, axis=0).astype(np.uint8) if len(ring) else np.array([240, 240, 244], np.uint8)
                patch = np.where(reg[..., None], plate[ya:yb, xa:xb], med)
                f[ya:yb, xa:xb] = patch
            after += bool(blobs(f))
        if enc:
            enc.stdin.write(f.tobytes())
    dec.wait()
    if enc:
        enc.stdin.close()
        enc.wait()
        tmp.replace(src)
    return f"{cid}: frames {n} · with pointer {hit} · still orange after fill {after}"


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--") and a != _cfg_path]
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(3) as ex:
        for line in ex.map(lambda c: run(c, "--probe" in sys.argv), args):
            print(line)
