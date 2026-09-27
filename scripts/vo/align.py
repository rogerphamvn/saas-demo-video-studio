#!/usr/bin/env python3
"""VO step 4 (grid-first): word timing per LINE (lines/<line>.wav) + the line's offset from placements.json ->
<vo_dir>/captions.json (words + 2-4-word meaning groups) + caption-groups.txt.

STATUS: SMOKE-TESTED (27/09 ProfitBase ran it with hub imports and a Vietnamese hard-pair table in the code. Generalised:
        pairs + group limits from project.json "captions", new --asr none (offline estimate) and --offline (cache only).
        Re-run here only with --asr none on --fake-tts output; the whisper path was not re-run after generalising)

  python scripts/vo/align.py --config project.json [--asr whisper|none] [--offline]

- whisper: OpenAI whisper-1 word timestamps per line (tts_vn.whisper_words), mapped onto the SCRIPT words with
  tts_vn.align_script_to_asr (screen text is always the script's text). Answers are cached in <vo_dir>/asr_cache.json,
  so a re-run costs nothing; --offline refuses to call the API on a cache miss. Key: env OPENAI_API_KEY (or ./.env).
- none: no ASR, words spread over each line by length (source "estimate") - for pipeline tests / drafts only.
- Groups: DP split of each clause into 2-4 word groups (<= captions.group_max_chars chars), never splitting a HARD pair
  ("so lieu", "lo hang"...), avoiding SOFT pairs. Pairs: captions.hard_pairs / captions.soft_pairs ("w1 w2" strings) or
  captions.pairs_file ({"hard": [...], "soft": [...]}); see config-examples/caption-pairs.vi.json.
- Check: joined caption words == script.txt word for word (diff 0) and groups == script without dashes -> exit 1 if not.
"""
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import tts_vn as g  # noqa: E402
from lib.config import load_config, read_script_txt  # noqa: E402

cfg, a = load_config(description=__doc__, extra=lambda ap: (
    ap.add_argument("--asr", choices=["whisper", "none"], default="whisper"),
    ap.add_argument("--offline", action="store_true", help="use asr_cache.json only; fail instead of calling the API")))
VO = cfg.p("vo_dir")
pl = json.loads((VO / "placements.json").read_text(encoding="utf-8"))
man = json.loads((VO / "raw" / "manifest.json").read_text(encoding="utf-8"))
script = read_script_txt(cfg.p("script_txt"))

cache = VO / "asr_cache.json"
asr_all = json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else {}
key = None
words_all, per_line = [], []
tot_match = tot_words = 0
for p in pl["lines"]:
    lid = p["line"]
    f = VO / p["file"]
    dur = g.read_pcm(f.read_bytes())
    dur = len(dur[0]) / 2 / dur[1]
    ws = g.estimate_words(script[lid], 0.0, dur)
    if a.asr == "whisper":
        if lid not in asr_all:
            if a.offline:
                sys.exit(f"--offline: {lid} not in {cache} - run without --offline (calls whisper-1, paid)")
            key = key or g.get_key("OPENAI_API_KEY")
            asr_all[lid] = g.whisper_words(f, key)
            cache.write_text(json.dumps(asr_all, ensure_ascii=False, indent=1), encoding="utf-8")
        asr = asr_all[lid]
        ratio, unmatched = g.align_script_to_asr(ws, asr, dur)
    else:
        asr, ratio, unmatched = [], 0.0, list(range(len(ws)))
    tot_match += round(ratio * len(ws))
    tot_words += len(ws)
    per_line.append({"line": lid, "matched_ratio": round(ratio, 3), "asr_text": " ".join(w["text"] for w in asr),
                     "unmatched": [ws[i]["text"] for i in unmatched] if a.asr == "whisper" else []})
    for w in ws:
        words_all.append({"text": w["text"], "start": w["start"] + p["startS"], "end": w["end"] + p["startS"], "line": lid})
    print(f"{lid} ratio {ratio:.3f} | ASR: {per_line[-1]['asr_text']}")
    if per_line[-1]["unmatched"]:
        print(f"     noi suy: {per_line[-1]['unmatched']}")

# ---- 2-4 word groups (DP; a HARD pair is never split, a SOFT pair costs a little) ----
norm = lambda t: re.sub(r"[^\w]", "", t.lower())  # noqa: E731
C = cfg.get("captions", {})
pairs = {"hard": C.get("hard_pairs", []), "soft": C.get("soft_pairs", [])}
if C.get("pairs_file"):
    pf = json.loads(cfg.rel(C["pairs_file"]).read_text(encoding="utf-8"))
    pairs = {"hard": pairs["hard"] + pf.get("hard", []), "soft": pairs["soft"] + pf.get("soft", [])}
HARD = {tuple(x.split()) for x in pairs["hard"] if x.strip()}
SOFT = {tuple(x.split()) for x in pairs["soft"] if x.strip()}
HARD -= SOFT
CG_CHARS, CG_WORDS = int(C.get("group_max_chars", 26)), int(C.get("group_max_words", 4))
SIZE_COST = {1: 6, 2: 0, 3: 0, 4: 2}


def gsplit(ws):
    n = len(ws)
    INF = float("inf")
    best = [INF] * (n + 1)
    prev = [0] * (n + 1)
    best[0] = 0
    for j in range(1, n + 1):
        for i in range(max(0, j - CG_WORDS), j):
            grp = ws[i:j]
            txt = " ".join(w["text"] for w in grp)
            if len(grp) > 1 and len(txt) > CG_CHARS:
                continue
            c = best[i]
            if i > 0:
                pr = (norm(ws[i - 1]["text"]), norm(ws[i]["text"]))
                c += 1000 if pr in HARD else 10 if pr in SOFT else 0
            c += SIZE_COST.get(len(grp), 4) if n > 1 else 0
            if c < best[j]:
                best[j], prev[j] = c, i
    out, j = [], n
    while j > 0:
        out.append((prev[j], j))
        j = prev[j]
    return out[::-1]


groups, split_hard = [], []
for lid in script:
    ws = [(k, w) for k, w in enumerate(words_all) if w["line"] == lid]
    clauses, cur = [], []
    for k, w in ws:
        cur.append((k, w))
        if re.search(r"[,:;.?!—]$", w["text"]) or w["text"] == "—":
            clauses.append(cur)
            cur = []
    if cur:
        clauses.append(cur)
    for c in clauses:
        seq = [w for _, w in c if w["text"] != "—"]
        ids = [k for k, w in c if w["text"] != "—"]
        if not seq:
            continue
        spans = gsplit(seq)
        for (a_, b), (a2, _) in zip(spans, spans[1:]):
            pr = (norm(seq[b - 1]["text"]), norm(seq[a2]["text"]))
            if pr in HARD:
                split_hard.append(pr)
        for a_, b in spans:
            grp = seq[a_:b]
            groups.append({"text": " ".join(w["text"] for w in grp), "startMs": round(grp[0]["start"] * 1000),
                           "endMs": round(grp[-1]["end"] * 1000), "line": lid, "wordIdx": ids[a_:b]})

# ---- text check: captions == script word for word ----
caps = g.to_captions(words_all)
joined = "".join(c["text"] for c in caps)
ref = " ".join(script[k] for k in script)
diff_words = sum(1 for x, y in zip(joined.split(), ref.split()) if x != y) + abs(len(joined.split()) - len(ref.split()))
grp_words = " ".join(x["text"] for x in groups).split()
ref_nodash = [w for w in ref.split() if w != "—"]
grp_diff = sum(1 for x, y in zip(grp_words, ref_nodash) if x != y) + abs(len(grp_words) - len(ref_nodash))
sizes = [len(x["text"].split()) for x in groups]
ratio_all = tot_match / tot_words if tot_words else 0.0
source = ("aligned-whisper" if ratio_all >= g.STRICT_MIN_RATIO else "aligned-whisper-lowconf") if a.asr == "whisper" else "estimate"
out = {"durationMs": round(pl["durationS"] * 1000), "source": source,
       "engine": man.get("engine", "vieneu"), "model": None, "voice": man.get("voice"), "sampleRate": pl["sampleRate"],
       "grid": {"bpm": pl["bpm"], "bar": pl["bar"], "t0": pl["t0"], "t0_note": pl["t0_note"]},
       "alignMode": ("whisper-1 per line (lines/Exx.wav) + offset placements.json" if a.asr == "whisper"
                     else "estimate per line (no ASR) + offset placements.json"),
       "matched_ratio": round(ratio_all, 3),
       "asr_word_count": sum(len(v) for v in asr_all.values()) if a.asr == "whisper" else 0, "perLine": per_line,
       "textCheck": {"script_words": len(ref.split()), "caption_words": len(joined.split()), "diff_words": diff_words,
                     "group_diff_words_excl_dash": grp_diff, "hard_pair_splits": split_hard,
                     "group_sizes": {str(s): sizes.count(s) for s in sorted(set(sizes))}},
       "captions": caps, "groups": groups}
(VO / "captions.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
(VO / "caption-groups.txt").write_text("\n".join(f"{x['startMs']/1000:7.2f}-{x['endMs']/1000:6.2f} {x['line']}  {x['text']}" for x in groups),
                                       encoding="utf-8")
print(f"matched_ratio all {ratio_all:.3f} | diff_words {diff_words} | group diff {grp_diff} | hard splits {split_hard} | sizes {out['textCheck']['group_sizes']}")
sys.exit(0 if diff_words == 0 and grp_diff == 0 else 1)
