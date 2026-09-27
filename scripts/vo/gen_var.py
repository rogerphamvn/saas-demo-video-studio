#!/usr/bin/env python3
"""Generate pronunciation VARIANTS for a few sentences (same VieNeu worker + voice). The script text never changes -
only the TTS input. Input: variants JSON [{tag, line, idx, text_tts}]. Output: <vo_dir>/raw_var/<tag>.wav + appends to
<vo_dir>/raw_var/variants_log.json (select_takes.py reads it).

STATUS: TESTED (27/09 ProfitBase: 3 variant rounds; generalised = venv/worker/vo paths from env + project.json only)

  python scripts/vo/gen_var.py --config project.json vo/variants1.json

Typical loop (27/09): measure.py -> asr_check.py on suspicious lines -> write variants (respelling, comma, split) ->
gen_var.py -> asr_check.py raw_var/*.wav -> pick in takes.json -> select_takes.py.
"""
import json
import os
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from lib.config import load_config  # noqa: E402

cfg, a = load_config(description=__doc__, extra=lambda ap: (
    ap.add_argument("variants", help="variants JSON (path, or name inside vo_dir)"),
    ap.add_argument("--vieneu-python", default=os.environ.get("VIENEU_PY", ""))))
PY, WORKER = a.vieneu_python, HERE / "vieneu_worker.py"
if not PY or not pathlib.Path(PY).exists():
    sys.exit(f"VieNeu python not found ('{PY}'): set env VIENEU_PY or --vieneu-python")
vo_dir = cfg.p("vo_dir")
vp = pathlib.Path(a.variants)
vp = vp if vp.exists() else vo_dir / a.variants
var = json.loads(vp.read_text(encoding="utf-8"))
voice = cfg.get2("vo.voice")
out = vo_dir / "raw_var"
tmp = out / "_tmp"
tmp.mkdir(parents=True, exist_ok=True)
(tmp / "s.json").write_text(json.dumps([v["text_tts"] for v in var], ensure_ascii=False), encoding="utf-8")
cmd = [PY, str(WORKER), "--in", str(tmp / "s.json"), "--outdir", str(tmp / "wav")] + (["--voice", voice] if voice else [])
p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
if p.returncode:
    sys.exit(p.stderr[-1500:])
meta = json.loads([ln for ln in p.stdout.splitlines() if ln.startswith("{")][-1])
for v, f, pk in zip(var, meta["files"], meta["peak_abs"]):
    shutil.move(f, out / f"{v['tag']}.wav")
    v["peak_abs"] = pk
    v["file"] = str(out / f"{v['tag']}.wav")
log = out / "variants_log.json"
old = json.loads(log.read_text(encoding="utf-8")) if log.exists() else []
log.write_text(json.dumps(old + var, ensure_ascii=False, indent=1), encoding="utf-8")
print("OK", [v["tag"] for v in var])
