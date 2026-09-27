#!/usr/bin/env python3
"""Choose the take of each sentence after the 2-ASR pronunciation QC. Rewrites <vo_dir>/raw/manifest.json in place:
file, text_tts, peak_abs, take, why (the original take is kept in file_orig / text_tts_orig, so re-running is safe).

STATUS: SMOKE-TESTED (27/09 ProfitBase: 8 sentences switched to a variant; generalised = the choice table moved out of the code
        into vo.takes_file, keys "<line>.<idx>"; re-run here on a synthetic manifest + 1 variant)

  python scripts/vo/select_takes.py --config project.json

vo.takes_file (default <vo_dir>/takes.json):  {"E02.0": {"tag": "E02.0-r2", "why": "take 1: both ASRs heard 'lai'..."}, ...}
Every tag must exist in <vo_dir>/raw_var/variants_log.json (gen_var.py). Sentences not listed go back to the original take.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.config import load_config, norm_line_id  # noqa: E402

cfg, _ = load_config(description=__doc__)
vo_dir = cfg.p("vo_dir")
tf = cfg.rel(cfg.get2("vo.takes_file", str(vo_dir / "takes.json")))
SEL = {}
for k, v in (json.loads(tf.read_text(encoding="utf-8")) if tf.exists() else {}).items():
    if k.startswith("_"):
        continue
    line, idx = k.rsplit(".", 1)
    SEL[(norm_line_id(line), int(idx))] = (v["tag"], v.get("why", ""))
man_p = vo_dir / "raw" / "manifest.json"
man = json.loads(man_p.read_text(encoding="utf-8"))
vl = vo_dir / "raw_var" / "variants_log.json"
var = {v["tag"]: v for v in json.loads(vl.read_text(encoding="utf-8"))} if vl.exists() else {}
missing = [t for t, _ in SEL.values() if t not in var]
if missing:
    sys.exit(f"takes file names variant tag(s) not in {vl}: {missing}")
for it in man["items"]:
    it.setdefault("file_orig", it["file"])
    it.setdefault("text_tts_orig", it["text_tts"])
    s = SEL.get((it["line"], it["idx"]))
    if s:
        v = var[s[0]]
        it.update(file=v["file"], text_tts=v["text_tts"], peak_abs=v["peak_abs"], take=s[0], why=s[1])
    else:
        it.update(file=it["file_orig"], text_tts=it["text_tts_orig"], take="goc")
man_p.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
print("OK", sum(1 for i in man["items"] if i["take"] != "goc"), "sentences use a variant take", f"({tf.name}: {len(SEL)} entries)")
