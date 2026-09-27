#!/usr/bin/env python3
"""conform_music.py - splice the measured music file onto the video's bar grid WITHOUT time-stretching: every output bar g
is one whole source bar ARR[g], cut on downbeats with an equal-power crossfade (music.crossfade_s, 30 ms) that ENDS on the
downbeat (the new bar's transient is never faded). Also writes the delayed VO and the grid (single timing source).

STATUS: SMOKE-TESTED (27/09 ProfitBase v3 ran the original with the arrangement / T0 / TAIL / drops / chapter bars / hard
        cuts and all paths as literals. Here those moved to project.json "grid" + "music"; same splice arithmetic. Re-run on a
        synthetic 124 BPM click track + fake VO; check_grid.py: 6 downbeats, max |delta| 1.6 ms)

  python scripts/music/conform_music.py --config project.json

Reads : paths.music_src (source music), <vo_dir>/voiceover.wav + placements.json (assemble.py), grid.* and music.*
Writes: <comp>/assets/audio/music-grid.wav (+ music-grid-<alt>.wav when music.arrangement_alt is set, ear A/B only),
        <comp>/assets/audio/vo.wav (VO delayed by grid.t0, padded to the video length),
        <comp>/data/grid.json + <comp>/data/grid.js (window.GRID - the engine reads it; format unchanged from 27/09).
Keys  : grid.bpm, grid.bars, grid.t0 (first downbeat, s), grid.tail_s, grid.fps, grid.drops [bar], grid.hard_cuts_bars,
        grid.chapters [{line, bars:[in,out], id?}], music.source_bpm (fit window +-0.1), music.arrangement [src bar per grid
        bar, len = grid.bars], music.crossfade_s, music.alt_name + music.arrangement_alt (optional variant).
Deterministic (no randomness). Needs ffmpeg + numpy + scipy (librosa avoided: hangs on Windows).
"""
import json
import pathlib
import re
import subprocess
import sys

import numpy as np
from scipy.io import wavfile
from scipy.ndimage import maximum_filter1d

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
SR = 48000


def decode(path, sr=SR, ch=2, af=None):
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-i", str(path)]
    if af:
        cmd += ["-af", af]
    cmd += ["-f", "f32le", "-ac", str(ch), "-ar", str(sr), "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
    return x.reshape(-1, ch) if ch > 1 else x


def onset_env(x_mono, sr, hop):
    n = len(x_mono) // hop
    r = np.sqrt((x_mono[: n * hop].reshape(n, hop) ** 2).mean(axis=1) + 1e-12)
    e = np.log(r + 1e-5)
    return np.maximum(0, np.diff(e, prepend=e[0]))


def kick_env(path, sr=22050, hop=64):
    low = decode(path, sr, 1, "lowpass=f=150,lowpass=f=150")
    full = decode(path, sr, 1)
    lo, fu = onset_env(low, sr, hop), onset_env(full, sr, hop)
    n = min(len(lo), len(fu))
    env = lo[:n] / (lo.max() + 1e-9) + 0.5 * fu[:n] / (fu.max() + 1e-9)
    return env, sr / hop, len(full) / sr


def fit_fine(env, fps, dur, bpm_lo, bpm_hi):
    best = None
    for bpm in np.arange(bpm_lo, bpm_hi + 1e-9, 0.002):
        beat = 60 / bpm
        b0s = np.arange(0, beat, 0.0005)
        k = np.arange(int((dur - beat) / beat) - 1)
        idx = np.clip(np.round((b0s[:, None] + beat * k[None, :]) * fps).astype(int), 0, len(env) - 1)
        s = maximum_filter1d(env, 3)[idx].mean(axis=1)
        j = int(s.argmax())
        if best is None or s[j] > best[0]:
            best = (float(s[j]), float(bpm), float(b0s[j]))
    return best[1], best[2]


def conform(cfg, arr, out_name, write_meta):
    comp, vo_dir = cfg.comp(), cfg.p("vo_dir")
    SRC = cfg.p("music_src")
    BPM = float(cfg.need("grid.bpm"))
    BPB = int(cfg.get2("grid.beats_per_bar", 4))
    BAR = BPB * 60.0 / BPM
    BARS = int(cfg.need("grid.bars"))
    DROPS = list(cfg.get2("grid.drops", []))
    T0 = float(cfg.get2("grid.t0", 0.25))
    TAIL = float(cfg.get2("grid.tail_s", 0.0))
    FPS = int(cfg.get2("grid.fps", 30))
    XF = float(cfg.get2("music.crossfade_s", 0.030))
    assert len(arr) == BARS, f"music arrangement has {len(arr)} bars, grid.bars = {BARS}"
    sb = float(cfg.get2("music.source_bpm", BPM))
    env, efps, sdur = kick_env(SRC)
    src_bpm, src_b0 = fit_fine(env, efps, sdur, sb - 0.1, sb + 0.1)
    src_bar = BPB * 60 / src_bpm
    print(f"source {SRC.name}: {sdur:.3f}s  fitted BPM {src_bpm:.3f}  BEAT0 {src_b0:.4f}s  bar {src_bar:.5f}s")
    music = decode(SRC)
    ns = len(music)
    dur = round((T0 + BARS * BAR + TAIL) * FPS) / FPS              # video length snapped to a frame
    N = int(round(dur * SR))
    out = np.zeros((N, 2))
    xf = int(round(XF * SR))
    rin = np.sin(np.linspace(0, np.pi / 2, xf))[:, None]
    rout = np.cos(np.linspace(0, np.pi / 2, xf))[:, None]
    runs = []                                                        # runs of consecutive source bars
    g = 0
    while g < BARS:
        m0, g0 = arr[g], g
        while g + 1 < BARS and arr[g + 1] == arr[g] + 1:
            g += 1
        runs.append((g0, g, m0))
        g += 1
    splices = []
    for i, (ga, gb, m0) in enumerate(runs):
        d_start = T0 + ga * BAR
        s_start = src_b0 + m0 * src_bar
        last = i == len(runs) - 1
        pre = T0 if i == 0 else XF                                   # first run carries the pre-roll
        d_end = dur if last else T0 + (gb + 1) * BAR                 # last run continues into the tail
        a_d, b_d = int(round((d_start - pre) * SR)), int(round(d_end * SR))
        a_s = int(round((s_start - pre) * SR))
        seg = np.zeros((b_d - a_d, 2))
        lo, hi = max(a_s, 0), min(a_s + (b_d - a_d), ns)
        seg[lo - a_s: hi - a_s] = music[lo:hi]
        if i == 0:
            k = int(0.15 * SR)                                       # soft pre-roll fade-in
            seg[:k] *= np.linspace(0, 1, k)[:, None]
        else:
            seg[:xf] *= rin
        if not last:
            seg[-xf:] *= rout
        else:
            k = int(0.4 * SR)
            seg[-k:] *= np.linspace(1, 0, k)[:, None]
        out[a_d:b_d] += seg
        if i > 0:
            splices.append({"bar": ga, "t": round(d_start, 4), "from_src_bar": runs[i - 1][2] + (runs[i - 1][1] - runs[i - 1][0]),
                            "to_src_bar": m0})
    peak = np.abs(out).max()
    print(f"output {dur:.4f}s  peak {20*np.log10(peak+1e-12):.2f} dBFS  runs {len(runs)}  splices {len(splices)}")
    (comp / "assets" / "audio").mkdir(parents=True, exist_ok=True)
    wavfile.write(comp / "assets" / "audio" / out_name, SR, (np.clip(out, -1, 1) * 32767).astype(np.int16))
    if not write_meta:
        return
    vo_src = vo_dir / "voiceover.wav"
    vo_sr, vo = wavfile.read(vo_src)
    assert vo_sr == SR, f"{vo_src} is {vo_sr} Hz, expected {SR}"
    vo_out = np.zeros(N, dtype=vo.dtype)
    off = int(round(T0 * SR))
    L = min(len(vo), N - off)
    vo_out[off: off + L] = vo[:L]
    wavfile.write(comp / "assets" / "audio" / "vo.wav", SR, vo_out)
    print(f"vo.wav: {vo_src.name} ({len(vo)/SR:.3f}s) delayed {T0}s -> {N/SR:.3f}s")
    place = {p["line"]: p for p in json.loads((vo_dir / "placements.json").read_text(encoding="utf-8"))["lines"]}
    chapters = []
    for c in cfg.need("grid.chapters"):
        a, b = c["bars"]
        from lib.config import norm_line_id  # noqa: PLC0415
        ln = place[norm_line_id(c["line"])]
        cid = c.get("id") or re.sub(r"^([A-Za-z]+)0*(\d+)$", r"\1\2", c["line"])
        chapters.append({"id": cid, "bar_in": a, "bar_out": b, "t_in": round(T0 + a * BAR, 4), "t_out": round(T0 + b * BAR, 4),
                         "vo_start": round(ln["startS"] + T0, 4), "vo_end": round(ln["endS"] + T0, 4)})
    chapters[-1]["t_out_video"] = dur
    rel = lambda p: p.relative_to(cfg.root).as_posix() if p.is_relative_to(cfg.root) else p.name  # noqa: E731
    grid = {"bpm": BPM, "bar_s": BAR, "beat_s": BAR / BPB, "t0": T0, "bars": BARS, "fps": FPS, "duration": dur, "tail_s": TAIL,
            "drops": DROPS, "drop_t": [round(T0 + d * BAR, 4) for d in DROPS],
            "bar_t": [round(T0 + k * BAR, 4) for k in range(BARS + 1)],
            "hard_cuts_bars": list(cfg.get2("grid.hard_cuts_bars", [])),
            "chapters": chapters,
            "music": {"file": "assets/audio/music-grid.wav", "source": rel(SRC),
                      "source_bpm_fit": round(src_bpm, 3), "source_beat0": round(src_b0, 4), "arrangement_src_bar_per_grid_bar": arr,
                      "splices": splices, "crossfade_s": XF, "method": "whole-bar splices on downbeats, no time-stretch"},
            "vo": {"file": "assets/audio/vo.wav", "source": rel(vo_src), "shift_s": T0}}
    (comp / "data").mkdir(parents=True, exist_ok=True)
    (comp / "data" / "grid.json").write_text(json.dumps(grid, ensure_ascii=False, indent=1), encoding="utf-8")
    (comp / "data" / "grid.js").write_text("/* generated by scripts/music/conform_music.py - DO NOT EDIT */\nwindow.GRID = "
                                           + json.dumps(grid, ensure_ascii=False) + ";\n", encoding="utf-8")
    print("wrote data/grid.json + data/grid.js")


if __name__ == "__main__":
    from lib.config import load_config  # noqa: E402

    cfg, _ = load_config(description=__doc__)
    conform(cfg, list(cfg.need("music.arrangement")), "music-grid.wav", True)
    if cfg.get2("music.arrangement_alt"):
        conform(cfg, list(cfg.get2("music.arrangement_alt")), f"music-grid-{cfg.get2('music.alt_name', 'alt')}.wav", False)
