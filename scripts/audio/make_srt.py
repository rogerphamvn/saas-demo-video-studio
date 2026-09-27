"""make_srt.py - <deliver_dir>/<name>.srt from the burned-in caption groups (<comp>/data/captions.js, which come from
<vo_dir>/captions.json groups + grid t0). Rules: text diff vs paths.script_txt = 0 (dash tokens excluded), no cue < srt.min_cue_s
(0.6 s: a short cue first borrows the silence after it, then before it; if still short it is merged with its shorter
neighbour in the same line). Proves every captions.js boundary is a captions.json group boundary + t0.

STATUS: SMOKE-TESTED (27/09 ProfitBase audio_srt_v3.py; generalised = paths / output name / min cue from project.json.
        Re-run here on align.py --asr none + make_captions_js.py output, see scripts/README.md)

  python scripts/audio/make_srt.py --config project.json [--out deliver/Name.srt]
"""
import json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.config import load_config  # noqa: E402

cfg, _a = load_config(description=__doc__, extra=lambda ap: ap.add_argument("--out", default=None))
ROOT = cfg.comp()
G = json.loads((ROOT / "data" / "grid.json").read_text(encoding="utf-8"))
C = json.loads((cfg.p("vo_dir") / "captions.json").read_text(encoding="utf-8"))
T0, MIN = G["t0"], float(cfg.get2("srt.min_cue_s", 0.6))
cues = [dict(text=g["text"], a=g["startMs"] / 1000 + T0, b=g["endMs"] / 1000 + T0, line=g["line"]) for g in C["groups"]]
n_in = len(cues)
# The burned-in track (data/captions.js, make_captions_js.py, read only) merges single-word groups (main 27/09 rule).
# The .srt must match the screen line for line -> take ITS grouping, and prove every boundary is a captions.json group
# boundary + t0 (so the timing source is still captions.json).
js = (ROOT / "data" / "captions.js").read_text(encoding="utf-8")
caps = json.loads(js[js.index("{"): js.rindex("}") + 1])
starts = {round(c["a"], 3) for c in cues}; ends = {round(c["b"], 3) for c in cues}
dmax = max(min(abs(g[1] - x) for x in starts) + min(abs(g[2] - x) for x in ends) for g in caps["groups"])
assert dmax < 0.011, f"captions.js boundary not on a captions.json group boundary: {dmax:.3f}s"
cues = [dict(text=g[0], a=g[1], b=g[2], line=g[3]) for g in caps["groups"]]
# 1) borrow silence after the cue
for i, c in enumerate(cues):
    if c["b"] - c["a"] < MIN:
        nxt = cues[i + 1]["a"] if i + 1 < len(cues) else G["duration"]
        c["b"] = min(c["a"] + MIN, nxt)
# 1b) then the silence before it (start earlier, never before the previous cue's end)
for i, c in enumerate(cues):
    if c["b"] - c["a"] < MIN:
        prv = cues[i - 1]["b"] if i else 0.0
        c["a"] = max(prv, c["b"] - MIN)
# 2) merge what is still short with the shorter neighbour of the same line
merged = 0
while True:
    short = [i for i, c in enumerate(cues) if c["b"] - c["a"] < MIN - 1e-6]
    if not short:
        break
    i = short[0]
    cand = [j for j in (i - 1, i + 1) if 0 <= j < len(cues) and cues[j]["line"] == cues[i]["line"]] or \
           [j for j in (i - 1, i + 1) if 0 <= j < len(cues)]
    nw = lambda j: len(cues[i]["text"].split()) + len(cues[j]["text"].split())
    j = min(cand, key=lambda j: (nw(j) > 4, nw(j), cues[j]["b"] - cues[j]["a"]))   # keep 2-4 words when possible
    a, b = sorted((i, j))
    cues[a] = dict(text=cues[a]["text"] + " " + cues[b]["text"], a=cues[a]["a"], b=cues[b]["b"], line=cues[a]["line"])
    del cues[b]
    merged += 1


def ts(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


out = pathlib.Path(_a.out) if _a.out else cfg.p("deliver_dir") / f"{cfg.get('project', 'video')}.srt"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("\n".join(f"{k}\n{ts(c['a'])} --> {ts(c['b'])}\n{c['text']}\n" for k, c in enumerate(cues, 1)), encoding="utf-8")
# checks
tok = lambda s: [w for w in s.split() if not re.fullmatch(r"[—–-]+", w)]
script = " ".join(l.split("|", 1)[1] for l in cfg.p("script_txt").read_text(encoding="utf-8").splitlines() if "|" in l)
sw, cw = tok(script), tok(" ".join(c["text"] for c in cues))
diff = sum(1 for x, y in zip(sw, cw) if x != y) + abs(len(sw) - len(cw))
durs = [c["b"] - c["a"] for c in cues]
ovl = sum(1 for p, q in zip(cues, cues[1:]) if q["a"] < p["b"] - 1e-6)
wc = [len(c["text"].split()) for c in cues]
print(f"{out.name}: groups {n_in} -> cues {len(cues)} (merged {merged}) | captions.js max drift {dmax * 1000:.1f} ms")
print(f"text diff vs script.txt: {diff} words ({len(sw)} script / {len(cw)} srt) | min cue {min(durs):.3f}s | overlaps {ovl} | words/cue {min(wc)}-{max(wc)} (>4: {sum(w > 4 for w in wc)})")
print(f"first {ts(cues[0]['a'])} last_end {ts(cues[-1]['b'])}")
print("SRT", "PASS" if diff == 0 and min(durs) >= MIN - 1e-6 and ovl == 0 else "FAIL")
sys.exit(0 if diff == 0 and min(durs) >= MIN - 1e-6 and ovl == 0 else 1)
