#!/usr/bin/env python3
"""check_grid.py - measure music-grid.wav against data/grid.json. KPI: every downbeat (kick) onset |delta| <= 40 ms.

READS: the OUTPUT wav + data/grid.json (+ the SOURCE wav only for the control column). The detector never reads the
arrangement to decide where a beat is, so it cannot "agree with itself".
KICK DETECTOR (KPI): band 40-110 Hz, RMS hop 32 @ 22.05 kHz (1.45 ms), 5-frame smoothing, positive log-energy derivative;
peaks >= 30% of the window max inside t_g +-80 ms; the peak NEAREST t_g is the measured downbeat. delta = peak - t_g.
CONTROL: the same detector on the SOURCE at the source bar used for that grid bar -> (delta_out - delta_src) isolates what the
splice did from what the music itself does (a kick that is late in the source is late in the output too).
INFO ONLY: a broadband "strongest peak in +-100 ms" detector (v2 fit-beat-grid envelope). It is noisy: it latches onto bass /
fills and reports +-60..96 ms inside UNSPLICED bars - kept so the reviewer sees why it is not the KPI.
STATUS: SMOKE-TESTED (27/09 ProfitBase original read fixed paths; generalised = paths from project.json, BPM fit window
        from grid.json; detector unchanged. Re-run on the synthetic conform_music.py output: KPI 6/6, max 1.6 ms)

  python scripts/music/check_grid.py --config project.json [--file <comp>/assets/audio/music-grid.wav] [--tol 0.040] > grid-check.txt
"""
import json, pathlib, sys
import numpy as np
from scipy.signal import find_peaks
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from conform_music import kick_env, fit_fine, decode  # noqa: E402
from lib.config import load_config  # noqa: E402


def kick_det(path, af="highpass=f=40,lowpass=f=110,lowpass=f=110"):
    x = decode(path, 22050, 1, af)
    hop = 32
    fps = 22050 / hop
    n = len(x) // hop
    r = np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
    r = np.convolve(r, np.ones(5) / 5, "same")
    e = np.maximum(0, np.diff(np.log(r + 1e-5), prepend=0))
    return e, fps, x


def nearest(e, fps, t, win=0.08):
    i0, i1 = int((t - win) * fps), int((t + win) * fps)
    w = e[max(i0, 0):i1]
    p, _ = find_peaks(w, height=0.3 * w.max())
    if len(p) == 0:
        return None
    tt = (max(i0, 0) + p) / fps
    return float(tt[np.argmin(np.abs(tt - t))] - t)


def main():
    cfg, a = load_config(description=__doc__, extra=lambda ap: (ap.add_argument("--file", default=None),
                                                                ap.add_argument("--tol", type=float, default=0.040)))
    a.file = a.file or str(cfg.comp("assets/audio/music-grid.wav"))
    G = json.loads(cfg.comp("data/grid.json").read_text(encoding="utf-8"))
    M = G["music"]
    src = cfg.rel(M["source"])
    sbar = 4 * 60 / M["source_bpm_fit"]
    eo, fo, xo = kick_det(a.file)
    es, fs, _ = kick_det(src)
    fo_e, fo_f, _ = kick_det(a.file, "anull")            # full-band detector for bars with NO kick (breakdown)
    fs_e, fs_f, _ = kick_det(src, "anull")
    benv, bfps, dur = kick_env(a.file)
    bpm, b0 = fit_fine(benv, bfps, dur, G["bpm"] - 0.2, G["bpm"] + 0.2)
    splice_bars = {s["bar"] for s in M["splices"]}
    lines = ["| bar | grid t (s) | src bar | kick delta OUT (ms) | kick delta SRC (ms) | OUT-SRC (ms) | broadband delta (ms, info) | kick-band RMS dB | verdict |",
             "|---|---|---|---|---|---|---|---|---|"]
    worst, fails, dbs = 0.0, 0, []
    for g in range(G["bars"]):
        t = G["bar_t"][g]
        m = M["arrangement_src_bar_per_grid_bar"][g]
        s0, s1 = int(t * 22050), int((t + G["bar_s"]) * 22050)
        kick_db = 20 * np.log10(np.sqrt(np.mean(xo[s0:s1] ** 2)) + 1e-9)
        nokick = kick_db < -45
        if nokick:        # breakdown bars: kick band is silent (< -45 dB) -> measure the full-band onset instead
            d = nearest(fo_e, fo_f, t)
            ds = nearest(fs_e, fs_f, M["source_beat0"] + m * sbar)
        else:
            d = nearest(eo, fo, t)
            ds = nearest(es, fs, M["source_beat0"] + m * sbar)
        i0, i1 = int((t - 0.1) * bfps), int((t + 0.1) * bfps)
        bb = (i0 + int(benv[i0:i1].argmax())) / bfps - t
        db = kick_db
        dbs.append(db)
        ok = d is not None and abs(d) <= a.tol
        fails += not ok
        worst = max(worst, abs(d) if d is not None else 9)
        tag = (" DROP" if g in G["drops"] else "") + (" splice" if g in splice_bars else "") + (" cut" if g in G["hard_cuts_bars"] else "") + (" NO-KICK:fullband" if nokick else "")
        lines.append(f"| {g}{tag} | {t:.3f} | M{m} | {d*1000:+.1f} | {ds*1000:+.1f} | {(d-ds)*1000:+.1f} | {bb*1000:+.1f} | {db:.1f} | {'PASS' if ok else 'FAIL'} |")
    head = [f"file {pathlib.Path(a.file).name} · {dur:.3f} s · global fit on OUTPUT: BPM {bpm:.3f}, beat phase {b0:.4f} s "
            f"(grid t0 = {G['t0']:.4f} s)",
            f"KICK KPI: {G['bars']} downbeats · max|delta| {worst*1000:.1f} ms (tol {a.tol*1000:.0f}) · FAIL {fails}",
            "drops, kick-band RMS prev bar -> drop bar: " + " · ".join(f"bar {d}: {dbs[d-1]:.1f} -> {dbs[d]:.1f} dB ({dbs[d]-dbs[d-1]:+.1f})" for d in G["drops"]),
            ""]
    print("\n".join(head + lines))


if __name__ == "__main__":
    main()
