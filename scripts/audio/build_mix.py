"""build_mix.py - SFX plan + music pick + ducked mix + master (-14 LUFS, TP <= -1) + KPI checks.
Same gain math as v2 build_mix.py (SFX peak frame rel_db under VO active RMS, margin boost capped by VO-9 under speech /
VO-5 in gaps, trim AFTER all gain math, music dip under hits that still sit < MARGIN over the bed).
v3 params (brief 27/09): SFX_TRIM_DB -4, MARGIN 3, MAX_EXTRA 6, caps VO-9 / VO-5 (hf-v3/scripts/mix_params.py still says
-2 = the v2 r2 value; this script does not import it so the v2 file is untouched).
Reads (never writes) <comp>/data/grid.json, data/cuts.json (if the plan uses `cut`), data/captions.js, paths.sfx_plan.
Writes <comp>/data/sfx-resolved.json (plan with resolved times), assets/audio/mix.wav/.m4a, assets/audio/mix-report.txt,
stems (vo/music/sfx/premaster .wav) -> paths.stems_dir (env MIX_STEMS overrides). Exit 1 if a KPI fails.

STATUS: SMOKE-TESTED (27/09 ProfitBase build_mix_v3.py. Generalised: the SFX plan list moved to a JSON file (paths.sfx_plan) with
        `at` anchors, params to project.json "mix" (defaults = the 27/09 values), music variant pick generic, guards for a
        plan without drops. ALL gain / duck / limiter / KPI math is unchanged. Re-run here on synthetic VO / music / 4 SFX:
        KPI 6/6 PASS, -14.0 LUFS. NOT re-run on the real ProfitBase stems.)

  python scripts/audio/build_mix.py --config project.json

SFX plan (see config-examples/sfx-plan.example.json):
  {"sfx_dir": "assets/audio/sfx", "events": [{"slot": "DROP 1", "at": {"drop": 1}, "offset": 0, "file": "slam", "rel_db": -11,
    "kind": "drop"}, ...]}
  at = {"t": s} | {"bar": n} | {"drop": n (1-based index into grid.drops)} | {"cut": "<clip id>"} (its t_in) |
       {"chapter": n (0-based) or "<id>"} (its t_in) | {"word": {"text": "tra", "line": "E02", "k": 1}} (k-th occurrence start)
  time = anchor + offset (s). file = a name in sfx_dir (".wav" added) or a path relative to the composition folder.
  kind: drop | tx (transition) | tick | brand (brand hit: exempt from the hot-word rule, always under the VO-9 ceiling).
Rules kept from 27/09: no SFX on the loudest VO word of a line (tick -> moved after it, tx -> removed, drop/brand kept);
SFX peak frame set rel_db under VO active RMS, + group boost, + up to MAX_EXTRA to reach MARGIN over the ducked music but
never above VO-9 (speech) / VO-5 (gaps); SFX_TRIM_DB applied AFTER all gain math; music dipped under hits still short
of MARGIN; master = gain + true-peak-aware limiter iterated to -14 LUFS, TP <= -1 dBTP on both wav and m4a.
"""
import json, pathlib, subprocess, re, sys, os
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.config import load_config, load_js_object, norm_line_id  # noqa: E402

cfg, _args = load_config(description=__doc__)
M_ = cfg.get("mix", {})
SFX_TRIM_DB, MARGIN_DB, MAX_EXTRA = float(M_.get("sfx_trim_db", -4.0)), float(M_.get("margin_db", 3.0)), float(M_.get("max_extra_db", 6.0))
CAP_SPEECH_DB, CAP_GAP_DB, PEAK_KPI_DB = float(M_.get("cap_speech_db", 9.0)), float(M_.get("cap_gap_db", 5.0)), float(M_.get("peak_kpi_db", -5.0))
GAP_DB, DUCK_DB = float(M_.get("music_gap_db", -6.0)), float(M_.get("music_duck_db", -23.0))
LUFS, TP_MAX = float(M_.get("lufs", -14.0)), float(M_.get("true_peak_db", -1.0))
ROOT = cfg.comp()
A = ROOT / "assets" / "audio"
SR = 48000
G = json.loads((ROOT / "data" / "grid.json").read_text(encoding="utf-8"))
_cuts_p = ROOT / "data" / "cuts.json"
CUTS = json.loads(_cuts_p.read_text(encoding="utf-8"))["clips"] if _cuts_p.exists() else {}
CAPS = load_js_object(ROOT / "data" / "captions.js")
DUR = G["duration"]; N = int(round(DUR * SR))
STEMS = pathlib.Path(os.environ["MIX_STEMS"]) if os.environ.get("MIX_STEMS") else cfg.p("stems_dir"); STEMS.mkdir(parents=True, exist_ok=True)
LOG = []
def log(s):
    print(s); LOG.append(s)


def dec(path, af=None):
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-i", str(path)] + (["-af", af] if af else []) + ["-f", "f32le", "-ac", "2", "-ar", str(SR), "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, dtype=np.float32).reshape(-1, 2).astype(np.float64)


def fit(x):
    out = np.zeros((N, 2)); out[: min(N, len(x))] = x[:N]; return out


def rms(a):
    return 20 * np.log10(np.sqrt(np.mean(a ** 2)) + 1e-12)


def W(word, line, k=1):
    cl = lambda w: re.sub(r"[^\w]", "", w.lower())
    hits = [w for w in CAPS["words"] if w[3] == norm_line_id(line) and cl(w[0]) == cl(word)]
    if len(hits) < k:
        raise SystemExit(f"SFX plan: word '{word}' #{k} not found in line {line} of captions.js")
    return hits[k - 1][1]


bar = lambda n: G["t0"] + n * G["bar_s"]

# ---------------- 1. SFX plan (paths.sfx_plan) ----------------
PLAN = json.loads(cfg.p("sfx_plan").read_text(encoding="utf-8"))
PLAN = {"events": PLAN} if isinstance(PLAN, list) else PLAN
S = str(PLAN.get("sfx_dir", "assets/audio/sfx")).rstrip("/") + "/"


def anchor(at):
    if "t" in at:
        return float(at["t"])
    if "bar" in at:
        return bar(float(at["bar"]))
    if "drop" in at:
        return G["drop_t"][int(at["drop"]) - 1]
    if "cut" in at:
        if at["cut"] not in CUTS:
            raise SystemExit(f"SFX plan: cut '{at['cut']}' not in data/cuts.json")
        return CUTS[at["cut"]]["t_in"]
    if "chapter" in at:
        c = at["chapter"]
        ch = G["chapters"][c] if isinstance(c, int) else next(x for x in G["chapters"] if x["id"] == c)
        return ch["t_in"]
    if "word" in at:
        w = at["word"]
        return W(w["text"], w["line"], int(w.get("k", 1)))
    raise SystemExit(f"SFX plan: unknown anchor {at}")


def sfx_file(f):
    return f if ("/" in f or f.endswith(".wav")) else S + f + ".wav"


SFX = [dict(slot=e["slot"], t=round(anchor(e["at"]) + float(e.get("offset", 0.0)), 4), file=sfx_file(e["file"]),
            rel_db=e["rel_db"], kind=e["kind"]) for e in PLAN["events"]]
for e in SFX:
    assert (ROOT / e["file"]).exists(), e["file"]

# no SFX on the highest-energy VO word of each chapter (peak 10 ms frame of the VO over the word span)
vo = fit(dec(A / "vo.wav"))
fr = 480
voe = np.sqrt((vo[: N // fr * fr] ** 2).reshape(-1, fr, 2).mean((1, 2)))
active = voe > 10 ** (-40 / 20)
vo_act = 20 * np.log10(np.sqrt((voe[active] ** 2).mean()))
hot = {}
for w in CAPS["words"]:
    if not w[3] or not re.search(r"\w", w[0]):
        continue
    a, b = int(w[1] * SR) // fr, max(int(w[1] * SR) // fr + 1, int(w[2] * SR) // fr)
    pk = voe[a:b].max()
    if w[3] not in hot or pk > hot[w[3]][0]:
        hot[w[3]] = (pk, w[0], w[1], w[2])
dropped = []
for e in list(SFX):
    for ln, (pk, word, a, b) in hot.items():
        if a - 0.05 <= e["t"] <= b:
            if e["kind"] == "brand":    # main 27/09: brand reveal is exempt from the hot-word rule (kept under VO-9 below)
                log(f"NOTE brand hit {e['t']:.3f} next to hot word '{word}' {ln} - kept (main exception)")
            elif e["kind"] == "drop":
                log(f"NOTE drop {e['t']:.3f} sits on hot word '{word}' {ln} [{a:.2f}-{b:.2f}] - drop kept (grid rule wins)")
            elif e["kind"] == "tick":   # a small tick just waits for the hot word to finish
                dropped.append(f"MOVED {e['slot']} {e['t']:.2f}->{b + 0.1:.2f} (hot word '{word}' {ln})"); e["t"] = round(b + 0.1, 4)
            else:                       # a transition hit ON the hot word is removed (the cut itself carries it)
                dropped.append(f"REMOVED {e['slot']} @ {e['t']:.2f} (hot word '{word}' {ln})"); SFX.remove(e)
            break
log(f"hot words (max VO peak per chapter): " + " · ".join(f"{ln}:{v[1]}@{v[2]:.2f}" for ln, v in sorted(hot.items())))
log(f"SFX hot-word rule actions: {len(dropped)} {dropped}")
(ROOT / "data" / "sfx-resolved.json").write_text(json.dumps({"_doc": "resolved SFX plan, built by scripts/audio/build_mix.py (t = video s; hit = audible onset)",
    "params": dict(SFX_TRIM_DB=SFX_TRIM_DB, MARGIN_DB=MARGIN_DB, MAX_EXTRA=MAX_EXTRA, cap_speech=f"VO-{CAP_SPEECH_DB:g}", cap_gap=f"VO-{CAP_GAP_DB:g}"),
    "sfx": SFX}, ensure_ascii=False, indent=1), encoding="utf-8")

# ---------------- 2. music pick: kick band (40-120 Hz) rise at drop 1 (main vs the optional alt arrangement) ----------------
def kick_rise(p):
    k = dec(p, "highpass=f=40,lowpass=f=120")
    D1 = G["drop_t"][0]
    pre, post = k[int(bar(G["drops"][0] - 1) * SR): int(D1 * SR)], k[int(D1 * SR): int(bar(G["drops"][0] + 1) * SR)]
    return rms(post) - rms(pre), rms(pre), rms(post)
MUSIC = "music-grid.wav"
ALT = f"music-grid-{cfg.get2('music.alt_name', 'alt')}.wav"
if G["drops"] and (A / ALT).exists():
    kr_main, kr_alt = kick_rise(A / MUSIC), kick_rise(A / ALT)
    log(f"kick 40-120 Hz bar before -> drop 1: {MUSIC} {kr_main[0]:+.1f} dB ({kr_main[1]:.1f}->{kr_main[2]:.1f}) | {ALT} {kr_alt[0]:+.1f} dB ({kr_alt[1]:.1f}->{kr_alt[2]:.1f})")
    rise = float(M_.get("drop_kick_rise_db", 6.0))
    MUSIC = MUSIC if kr_main[0] >= rise else ALT
    log(f"MUSIC CHOSEN: {MUSIC} (rule: main rise < +{rise:g} dB -> alt)")
else:
    log(f"MUSIC: {MUSIC} (no alt arrangement file or no drops)")
music = fit(dec(A / MUSIC))

# ---------------- 3. ducking ----------------
t = np.arange(N) / SR
speech = np.zeros(N, bool)
for g in CAPS["groups"]:
    speech[int(max(g[1] - 0.15, 0) * SR): int(min(g[2] + 0.15, DUR) * SR)] = True
target = np.where(speech, DUCK_DB, GAP_DB)
k = int(0.25 * SR)
_c = np.concatenate([[0.0], np.cumsum(np.pad(target, (k // 2, k - 1 - k // 2), mode="edge"))])
env_db = (_c[k:] - _c[:-k]) / k
music_d = music * (10 ** (env_db / 20))[:, None]
music_d *= np.clip((DUR - t) / 1.5, 0, 1)[:, None]          # 1.5 s fade at the very end

# ---------------- 4. SFX placement (v2 math) ----------------
sfx = np.zeros((N, 2)); rep = []
GROUP_BOOST = {k: float(v) for k, v in M_.get("group_boost", {"flip": 5.0, "diagram": 5.0, "chart-rise": 5.0, "typing": 6.0}).items()}
W03 = int(0.3 * SR)
def margin(sf, mu):
    return min(rms(sf) - rms(mu), rms(sf.mean(axis=1)) - rms(mu.mean(axis=1)))
for e in SFX:
    x = dec(ROOT / e["file"])
    xe = np.sqrt((x[: len(x) // fr * fr].reshape(-1, fr, 2) ** 2).mean((1, 2)))
    x_act = 20 * np.log10(xe.max())
    base = e["file"].split("/")[-1][:-4]
    boost = next((v for kk, v in GROUP_BOOST.items() if base.startswith(kk)), 0.0)
    g = 10 ** ((vo_act + e["rel_db"] + boost - x_act) / 20)
    onset = float(np.argmax(xe >= xe.max() * 0.1)) * fr / SR
    i0 = int(round((e["t"] - onset) * SR))
    if i0 < 0:
        x, i0 = x[-i0:], 0
    n = min(len(x), N - i0)
    cs = np.concatenate([[0.0], np.cumsum((x[:n] ** 2).mean(1))])
    wl = min(W03, n); j = min(int(onset * SR), max(0, n - wl))
    own = 10 * np.log10((cs[j + wl] - cs[j]) / wl * g * g + 1e-24)
    bed = rms(music_d[i0 + j: i0 + j + wl])
    peak_now = x_act + 20 * np.log10(g)
    speaking = rms(vo[i0 + j: i0 + j + wl]) > vo_act - 15.0 or e["kind"] == "brand"   # brand hit: always VO-9 ceiling
    room = (vo_act - (CAP_SPEECH_DB if speaking else CAP_GAP_DB)) - peak_now
    extra = max(0.0, min(MAX_EXTRA, bed + MARGIN_DB + 0.5 - own, room))
    g *= 10 ** ((extra + SFX_TRIM_DB) / 20)
    sfx[i0: i0 + n] += x[:n] * g
    e["_eff_db"] = round(e["rel_db"] + boost + extra + SFX_TRIM_DB, 1)
    rep.append((e, (i0 + j, wl), speaking))
duck = np.zeros(N)
for e, (a, wl), _ in rep:
    need = MARGIN_DB + 0.5 - margin(sfx[a:a + wl], music_d[a:a + wl])
    if need > 0:
        lo, hi = max(0, a - int(0.05 * SR)), min(N, a + wl + int(0.1 * SR))
        duck[lo:hi] = np.minimum(duck[lo:hi], -min(24.0, need))
r = int(0.05 * SR)
_c = np.concatenate([[0.0], np.cumsum(np.pad(duck, (r // 2, r - 1 - r // 2), mode="edge"))])
duck = (_c[r:] - _c[:-r]) / r
music_d = music_d * (10 ** (duck / 20))[:, None]
log(f"music dipped under {(duck < -0.5).sum() / SR:.1f} s of SFX hits (max {duck.min():.1f} dB)")
mix = vo + music_d + sfx


def wr(p, x, extra=()):
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "f64le", "-ac", "2", "-ar", str(SR), "-i", "-", *extra, str(p)],
                   input=x.astype(np.float64).tobytes(), check=True)
for nm, x in (("vo", vo), ("music", music_d), ("sfx", sfx), ("premaster", mix)):
    wr(STEMS / f"{nm}.wav", x)

# ---------------- 5. master: gain + true-peak-aware limiter, iterate to -14 LUFS ----------------
def ebu(path):
    o = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    o = o[o.rindex("Summary"):]
    f = lambda pat: float(re.search(pat, o).group(1))
    return f(r"I:\s+(-?[\d.]+) LUFS"), f(r"Peak:\s+(-?[\d.]+) dBFS"), f(r"LRA:\s+(-?[\d.]+) LU")
pm = STEMS / "premaster.wav"
wav, m4a = STEMS / "mix.wav", STEMS / "mix.m4a"   # built in temp, copied to assets/audio at the end (file may be locked by a preview)
i_in, tp_in, _ = ebu(pm)
gain, lim = LUFS - i_in, 0.70   # limiter ceiling 0.70 (-3.1 dBFS sample) leaves room for inter-sample + AAC overshoot
for it in range(5):
    af = f"volume={gain:.2f}dB,aresample=192000,alimiter=limit={lim}:attack=2:release=60:level=disabled,aresample={SR}"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(pm), "-af", af, "-ar", str(SR), "-ac", "2", "-c:a", "pcm_s24le",
                    "-t", f"{DUR}", str(wav)], check=True)
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(wav), "-c:a", "aac", "-b:a", "256k", "-t", f"{DUR}", str(m4a)], check=True)
    I, TP, LRA = ebu(m4a); Iw, TPw, _ = ebu(wav)
    log(f"master iter {it}: gain {gain:+.2f} dB limit {lim} -> m4a I {I} TP {TP} LRA {LRA} | wav I {Iw} TP {TPw}")
    ok_i, ok_tp = abs(I - LUFS) <= 0.3, max(TP, TPw) <= TP_MAX
    if ok_i and ok_tp:
        break
    if not ok_tp:
        lim = round(lim * 10 ** ((TP_MAX - 0.2 - max(TP, TPw)) / 20), 3)
    gain += LUFS - I

# ---------------- 6. checks ----------------
def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True).stdout.strip())
sf_fr = np.sqrt((sfx[: N // fr * fr].reshape(-1, fr, 2) ** 2).mean((1, 2)))
worst, mg, dro = [], [], []
for e, (a, wl), sp in rep:
    a10, b10 = int(max(e["t"], 0) * SR) // fr, int((e["t"] + 0.6) * SR) // fr
    worst.append((20 * np.log10(sf_fr[a10:b10].max() + 1e-12) - vo_act, e["slot"], e["t"], sp))
    mg.append((margin(sfx[a:a + wl], music_d[a:a + wl]), e["slot"], e["t"]))
    if e["kind"] == "drop":   # audible onset in the SFX stem (first 10 ms frame >= 10% of the local peak) vs grid drop
        s0 = int((e["t"] - 0.15) * SR) // fr; seg = sf_fr[s0: s0 + int(0.5 * SR) // fr]
        on = (s0 + int(np.argmax(seg >= seg.max() * 0.1))) * fr / SR
        dro.append((on - e["t"]) * 1000)
over = [(round(d, 1), s, round(t_, 2)) for d, s, t_, sp in worst if d > PEAK_KPI_DB]
over_sp = [(round(d, 1), s, round(t_, 2)) for d, s, t_, sp in worst if sp and d > -CAP_SPEECH_DB + 0.05]
log(f"VO active RMS {vo_act:.1f} dBFS | SFX {len(rep)} events | peak vs VO: max {max(worst)[0]:+.1f} dB ({max(worst)[1]} @ {max(worst)[2]:.2f}) | over VO{PEAK_KPI_DB:+g}: {len(over)} {over}")
log(f"SFX under speech over VO-{CAP_SPEECH_DB:g}: {len(over_sp)} {over_sp}")
log(f"SFX margin over music (0.3 s, min stereo/mono): min {min(mg)[0]:+.1f} dB ({min(mg)[1]} @ {min(mg)[2]:.2f}) | < +{MARGIN_DB:g}: {sum(m[0] < MARGIN_DB for m in mg)}")
log(f"drop onsets vs grid (ms): {[round(d, 1) for d in dro]} | max |d| {max([abs(d) for d in dro] or [0]):.1f} ms (<= 20)")
Dw, Dm = dur(wav), dur(m4a)
log(f"length: mix.wav {Dw:.3f} s | mix.m4a {Dm:.3f} s (target {DUR} +-0.05)")
kpi = dict(I=abs(I - LUFS) <= 0.5, TP=max(TP, TPw) <= TP_MAX, peak=not over, speech_cap=not over_sp, drops=max([abs(d) for d in dro] or [0]) <= 20,
           length=abs(Dw - DUR) <= 0.05 and abs(Dm - DUR) <= 0.05)
log("KPI " + " · ".join(f"{k_}={'PASS' if v else 'FAIL'}" for k_, v in kpi.items()))
for e, *_ in rep:
    log(f"  {e['t']:7.3f}  {e['file'].split('/')[-1]:<12} rel {e['rel_db']:>4} eff {e['_eff_db']:>6}  {e['slot']}")
import shutil, time
for src in (wav, m4a):
    for k_try in range(10):
        try:
            shutil.copyfile(src, A / src.name); break
        except PermissionError:
            time.sleep(3)
    else:
        log(f"COPY FAIL {src.name} -> assets/audio (locked) - file left in {src}"); kpi["copy"] = False
log(f"written: " + ", ".join(f"{(A / p_).name} {(A / p_).stat().st_size // 1024} KB" for p_ in ("mix.wav", "mix.m4a") if (A / p_).exists()))
(A / "mix-report.txt").write_text("\n".join(LOG) + "\n", encoding="utf-8")
sys.exit(0 if all(kpi.values()) else 1)
