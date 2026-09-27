"""Shared audio / video / pointer / HTML-marker helpers for the scripts in scripts/.

STATUS: TESTED (hub copy used by the 26/09 ProfitBase QA scripts; here only the config part now delegates to lib/config.py)

Config loading lives in lib/config.py (one loader for every script); `load_config`, `Cfg` and `out_dir` are re-exported
here so older scripts keep working.
"""
import json  # noqa: F401
import pathlib  # noqa: F401
import re
import subprocess
import wave

import numpy as np

HOP = 0.010  # s, VO envelope hop


# ---------------------------------------------------------------- config (delegates to lib/config.py)
from lib.config import Cfg, load_config  # noqa: E402,F401  (re-export)


def out_dir(cfg):
    d = cfg.p("qa_dir")
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------- text
def norm(t):
    """lower-case word without punctuation (keeps Vietnamese letters and '-')."""
    return re.sub(r"[^\w\-]", "", t.lower(), flags=re.UNICODE)


def fr(t, fps):
    """snap a time to the frame grid."""
    return round(round(t * fps) / fps, 4)


# ---------------------------------------------------------------- audio
def load_wav_mono16(path):
    with wave.open(str(path), "rb") as w:
        assert w.getsampwidth() == 2 and w.getnchannels() == 1, f"{path}: expect mono s16 WAV"
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    return x, sr


def env_db(x, sr, smooth=3):
    n = int(sr * HOP)
    m = len(x) // n
    f = x[: m * n].astype(np.float64).reshape(m, n) / 32768.0
    rms = np.sqrt((f ** 2).mean(axis=1)) + 1e-9
    if smooth > 1:
        rms = np.convolve(rms, np.ones(smooth) / smooth, mode="same")
    return 20 * np.log10(rms)


def silences(db, thr=-45.0, min_len=0.10):
    out, start = [], None
    for i, v in enumerate(db):
        if v < thr and start is None:
            start = i
        elif v >= thr and start is not None:
            if (i - start) * HOP >= min_len:
                out.append((start * HOP, i * HOP))
            start = None
    if start is not None and (len(db) - start) * HOP >= min_len:
        out.append((start * HOP, len(db) * HOP))
    return out


def decode_stereo(path, sr=48000, ss=0.0):
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", str(ss), "-i", str(path), "-f", "f32le",
                          "-ac", "2", "-ar", str(sr), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).astype(np.float64)


def rms_db(a):
    return 20 * np.log10(np.sqrt(np.mean(a ** 2)) + 1e-12)


# ---------------------------------------------------------------- pointer (recording's own cursor) detector
DEFAULT_POINTER_RULE = {  # the Claude-in-Chrome extension's muted-orange pointer (measured 26/09/2026)
    "r": [175, 240], "g": [95, 155], "b": [70, 135], "r_minus_g": [50, 105], "g_minus_b": [5, 45],
    "min_px": 40, "max_px": 2500, "max_std": 25, "bin": 48,
}


def color_mask(img, rule):
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    m = (r >= rule["r"][0]) & (r <= rule["r"][1]) & (g >= rule["g"][0]) & (g <= rule["g"][1]) \
        & (b >= rule["b"][0]) & (b <= rule["b"][1])
    if "r_minus_g" in rule:
        m &= (r - g >= rule["r_minus_g"][0]) & (r - g <= rule["r_minus_g"][1])
    if "g_minus_b" in rule:
        m &= (g - b >= rule["g_minus_b"][0]) & (g - b <= rule["g_minus_b"][1])
    return m


def detect_pointer(img, rule=None):
    """img: HxWx3 int16. Returns {"tip":[x,y], "bbox":[x0,y0,x1,y1], "n":px} or None."""
    rule = {**DEFAULT_POINTER_RULE, **(rule or {})}
    H_, W_ = img.shape[:2]
    ys, xs = np.nonzero(color_mask(img, rule))
    if len(xs) < rule["min_px"]:
        return None
    B = rule["bin"]
    Hh, xe, ye = np.histogram2d(xs, ys, bins=[np.arange(0, W_ + B, B), np.arange(0, H_ + B, B)])
    i, j = np.unravel_index(np.argmax(Hh), Hh.shape)
    sel = (xs >= xe[max(i - 1, 0)]) & (xs < xe[min(i + 2, len(xe) - 1)]) & (ys >= ye[max(j - 1, 0)]) & (ys < ye[min(j + 2, len(ye) - 1)])
    xs, ys = xs[sel], ys[sel]
    if not (rule["min_px"] <= len(xs) <= rule["max_px"] and xs.std() < rule["max_std"] and ys.std() < rule["max_std"]):
        return None
    ty = int(ys.min())
    tx = int(xs[ys <= ty + 2].min())
    return {"tip": [tx, ty], "bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())], "n": int(len(xs))}


def stream_frames(path, w, h, vf=None, ss=None, t=None, fps=None, n=None):
    """yield HxWx3 uint8 frames from ffmpeg (no whole-clip buffer)."""
    cmd = ["ffmpeg", "-nostdin", "-v", "error"]
    if ss is not None:
        cmd += ["-ss", f"{ss:.3f}"]
    if t is not None:
        cmd += ["-t", f"{t:.3f}"]
    cmd += ["-i", str(path)]
    filt = ",".join(x for x in ([f"fps={fps}"] if fps else []) + ([vf] if vf else []) if x)
    if filt:
        cmd += ["-vf", filt]
    if n:
        cmd += ["-frames:v", str(n)]
    cmd += ["-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    size = w * h * 3
    while True:
        buf = proc.stdout.read(size)
        if len(buf) < size:
            break
        yield np.frombuffer(buf, np.uint8).reshape(h, w, 3)
    proc.wait()


# ---------------------------------------------------------------- index.html marker injection
def inject(html_text, begin, end, payload):
    """Replace the text between two markers (kept). Raises if the markers are missing (silent no-op = bug)."""
    pat = re.escape(begin) + r".*?" + re.escape(end)
    new, n = re.subn(pat, lambda m: begin + payload + end, html_text, flags=re.S)
    if n != 1:
        raise AssertionError(f"marker {begin} ... {end} found {n} times (need exactly 1)")
    return new


def set_duration_attr(html_text, element_id, duration):
    """Set data-duration ONLY on one element id (never a global replace: that stretched every <video> and made
    the b-roll cover the whole film - ProfitBase round 5)."""
    pat = r'(<[a-z]+ id="' + re.escape(element_id) + r'"[^>]*?data-duration=")[0-9.]+(")'
    new, n = re.subn(pat, lambda m: m.group(1) + str(duration) + m.group(2), html_text)
    if n != 1:
        raise AssertionError(f'data-duration on id="{element_id}" found {n} times (need exactly 1)')
    return new
