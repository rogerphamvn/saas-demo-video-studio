#!/usr/bin/env python3
"""VO steps 1b-3 (grid-first): join the sentences of each line -> <vo_dir>/lines/<line>.wav, report fit per chapter
(fit.json), place every line on its chapter's first bar of the music grid -> <vo_dir>/voiceover.wav + placements.json.

STATUS: TESTED (27/09 ProfitBase VO v3; generalised = BPM / bar count / chapter->bar table / pads / adjust file from
        project.json instead of literals; same arithmetic. Also smoke-run here on --fake-tts output)

  python scripts/vo/assemble.py --config project.json

Grid: bar = beats_per_bar * 60 / grid.bpm (124 BPM -> 1.93548 s), grid.bars bars. placements.json times are on the grid
with t0 = 0 (nominal); conform_music.py shifts the whole VO by grid.t0 later.
Sentence join = like tts_vn.py (vo.gap_s = 250 ms between sentences) but each sentence is trimmed to its measured speech
(measure.py on/off, pads vo.pre_pad 20 ms / vo.post_pad 50 ms) so line lengths are real.
Per-line fixes (vo.adjust_file, default <vo_dir>/adjust.json), applied in the order the 27/09 brief gave:
  {"E05": {"atempo": 1.06, "gap_s": 0.12, "inner_pause_cap": 0.18, "start_shift_s": -0.50, "why": "..."}}
  a) atempo <= vo.max_atempo (1.06)  b) shorter gaps / capped inner pauses  c) spill into / shift against the bar.
Every fix is written to fit.json notes. A line that starts < vo.min_line_gap after the previous one is pushed later.
"""
import json
import pathlib
import subprocess
import sys
import wave

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
from lib.config import load_config, norm_line_id  # noqa: E402
from measure import env_db, load  # noqa: E402

cfg, _ = load_config(description=__doc__)
VO = cfg.p("vo_dir")
BPM = float(cfg.need("grid.bpm"))
BAR = int(cfg.get2("grid.beats_per_bar", 4)) * 60 / BPM
BARS = int(cfg.need("grid.bars"))
PRE_PAD, POST_PAD = float(cfg.get2("vo.pre_pad", 0.02)), float(cfg.get2("vo.post_pad", 0.05))
GAP_S = float(cfg.get2("vo.gap_s", 0.25))              # silence between sentences of one line (= tts_vn --gap-ms 250)
MIN_LINE_GAP = float(cfg.get2("vo.min_line_gap", 0.25))  # minimum breath between two lines
MAX_ATEMPO = float(cfg.get2("vo.max_atempo", 1.06))
TH_DB = float(cfg.get2("vo.th_db", -45.0))
CHAP = {norm_line_id(c["line"]): tuple(c["bars"]) for c in cfg.need("grid.chapters")}
adj_p = cfg.rel(cfg.get2("vo.adjust_file", str(VO / "adjust.json")))
ADJ = json.loads(adj_p.read_text(encoding="utf-8")) if adj_p.exists() else {}
ADJ = {norm_line_id(k): v for k, v in ADJ.items() if not k.startswith("_")}


def cap_inner_pauses(x, sr, cap):
    """shorten every silence INSIDE the sentence that is longer than cap (s) down to cap (cut the middle, keep both edges)."""
    e = env_db(x, sr)
    sil = e <= TH_DB
    keep = np.ones(len(x), bool)
    saved = 0.0
    i = 0
    on = np.where(~sil)[0]
    lo, hi = (on[0], on[-1]) if len(on) else (0, len(e))
    while i < len(e):
        if sil[i] and lo < i < hi:
            j = i
            while j < len(e) and sil[j]:
                j += 1
            L = (j - i) * 0.01
            if L > cap:
                cut = L - cap
                a = (i * 0.01 + cap / 2)
                b = a + cut
                keep[int(a * sr): int(b * sr)] = False
                saved += cut
            i = j
        else:
            i += 1
    return x[keep], saved


def atempo(x, sr, t, tag):
    tmp_in, tmp_out = VO / "lines" / f"_{tag}_in.wav", VO / "lines" / f"_{tag}_out.wav"
    save(tmp_in, x, sr)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp_in), "-filter:a", f"atempo={t}", "-ar", str(sr),
                    "-ac", "1", "-c:a", "pcm_s16le", str(tmp_out)], check=True)
    y, _ = load(tmp_out)
    tmp_in.unlink()
    tmp_out.unlink()
    return y


def save(f, x, sr):
    with wave.open(str(f), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


man = json.loads((VO / "raw" / "manifest.json").read_text(encoding="utf-8"))
sr = man["rate"]
(VO / "lines").mkdir(exist_ok=True)
lines = {}
for it in man["items"]:
    lines.setdefault(it["line"], []).append(it)
missing = [lid for lid in lines if lid not in CHAP]
if missing:
    sys.exit(f"grid.chapters has no bars for line(s) {missing} (chapters: {list(CHAP)})")

rows, place, prev_end = [], [], -1e9
full = np.zeros(int(sr * (BARS * BAR + 3)), np.float32)
for lid, its in lines.items():
    adj = ADJ.get(lid, {})
    gap = adj.get("gap_s", GAP_S)
    parts, notes = [], []
    for k, it in enumerate(its):
        x, _ = load(it["file"])
        a, b = max(0.0, it["on"] - PRE_PAD), min(len(x) / sr, it["off"] + POST_PAD)
        seg = x[int(a * sr): int(b * sr)]
        if "inner_pause_cap" in adj:
            seg, saved = cap_inner_pauses(seg, sr, adj["inner_pause_cap"])
            if saved > 0.005:
                notes.append(f"cau {k + 1}: rut khoang lang trong cau > {adj['inner_pause_cap']:.2f}s, bot {saved:.2f}s")
        parts.append(seg)
        if k < len(its) - 1:
            parts.append(np.zeros(int(sr * max(0.0, gap - PRE_PAD - POST_PAD)), np.float32))
    y = np.concatenate(parts)
    nat_len = sum(it["off"] - it["on"] for it in its) + GAP_S * (len(its) - 1) + PRE_PAD + POST_PAD
    if gap != GAP_S:
        notes.append(f"khoang lang giua cau {GAP_S * 1000:.0f} -> {gap * 1000:.0f} ms")
    t = adj.get("atempo", 1.0)
    if t != 1.0:
        assert t <= MAX_ATEMPO, (lid, t, f"atempo > vo.max_atempo {MAX_ATEMPO}")
        y = atempo(y, sr, t, lid)
        notes.insert(0, f"atempo {t}")
    save(VO / "lines" / f"{lid}.wav", y, sr)
    dur = len(y) / sr
    b_in, b_out = CHAP[lid]
    slot = (b_out - b_in) * BAR
    grid_in = b_in * BAR
    shift = adj.get("start_shift_s", 0.0)
    start = grid_in + shift
    if shift:
        notes.append(f"bat dau lech o {shift:+.2f}s so voi dau o {b_in}")
    if start < prev_end + MIN_LINE_GAP:
        d = prev_end + MIN_LINE_GAP - start
        start += d
        notes.append(f"lui {d:+.2f}s de cach dong truoc {MIN_LINE_GAP}s")
    end = start + dur
    s0 = int(start * sr)
    full[s0: s0 + len(y)] += y
    spill = end - (b_out * BAR)
    rows.append(dict(line=lid, bars=f"{b_in}-{b_out}", slot=round(slot, 3), natural=round(nat_len, 3), final=round(dur, 3),
                     diff_natural=round(nat_len - slot, 3), diff_final=round(dur - slot, 3), start=round(start, 3),
                     end=round(end, 3), grid_in=round(grid_in, 3), grid_out=round(b_out * BAR, 3),
                     spill_next=round(spill, 3), notes=notes))
    place.append({"line": lid, "startS": round(start, 4), "endS": round(end, 4), "barIn": b_in, "barOut": b_out,
                  "offsetFromBarS": round(start - grid_in, 4), "atempo": t, "file": f"lines/{lid}.wav"})
    prev_end = end

total = max(BARS * BAR, prev_end + 0.3)
full = full[: int(total * sr)]
peak = float(np.max(np.abs(full)))
save(VO / "voiceover.wav", full, sr)
bpm_out = int(BPM) if BPM == int(BPM) else BPM
json.dump({"bpm": bpm_out, "bar": BAR, "bars": BARS, "t0": 0.0, "t0_note": "chua do - dich theo grid.json khi co",
           "sampleRate": sr, "durationS": round(total, 3), "peak": round(peak, 4), "lines": place},
          open(VO / "placements.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(rows, open(VO / "fit.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for r in rows:
    print(f"{r['line']} o {r['bars']:>5} slot {r['slot']:5.2f} tu-nhien {r['natural']:5.2f} ({r['diff_natural']:+.2f}) "
          f"cuoi {r['final']:5.2f} ({r['diff_final']:+.2f}) @ {r['start']:6.2f}-{r['end']:6.2f} tran {r['spill_next']:+.2f} {'; '.join(r['notes'])}")
print(f"voiceover.wav {total:.2f}s peak {peak:.3f}")
