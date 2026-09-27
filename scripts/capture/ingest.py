"""ingest.py - append a PACKED macro log (one line per step, pipe-separated) to the capture log (JSON Lines).

STATUS: SMOKE-TESTED (27/09 version hard-coded the epoch base 1790500000 and wrote ./capture-log.jsonl; the base is now
        --epoch-base or derived from the clock, the log path is an arg - re-run here on a synthetic packed log)

  <packed lines> | python scripts/capture/ingest.py <shot> <take> [--log footage/capture-log.jsonl] [--epoch-base N]

Packed line = `step|action|t|bbox|value|selector`
  t     = Date.now()/1000 MODULO 100000 (short enough to copy out of a javascript_tool result); the full epoch is
          rebuilt as epoch_base + t. epoch_base default = the current clock floored to 100000 s (one step back if that
          would put the event in the future) - pass --epoch-base when ingesting a log older than ~1 day.
  bbox  = x,y,w,h (CSS px, getBoundingClientRect) -> [x, y, w, h]
  value = for action `readback`: the read value followed by a check mark / cross (ok true/false)
Macro mode (SKILL 5.0): the shot's JS macro collects these lines in window.__log; copy them out after rec_stop.
"""
import argparse
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.config import read_config, utf8_stdout  # noqa: E402

utf8_stdout()
ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("shot")
ap.add_argument("take")
ap.add_argument("--log", default=None, help="default: paths.capture_log")
ap.add_argument("--epoch-base", type=float, default=None)
ap.add_argument("--config", default=None)
a = ap.parse_args()
cfg = read_config(a.config or "project.json", required=bool(a.config))
log = pathlib.Path(a.log) if a.log else cfg.p("capture_log")
log.parent.mkdir(parents=True, exist_ok=True)
now = time.time()
base = a.epoch_base if a.epoch_base is not None else float(int(now // 1e5) * 1e5)
OK, BAD = "✓", "✗"
n = 0
with open(log, "a", encoding="utf-8") as f:
    for line in sys.stdin.buffer.read().decode("utf-8").splitlines():
        if not line.strip():
            continue
        s, act, t, bb, v, sel = (line.split("|") + [""] * 6)[:6]
        te = base + float(t)
        if a.epoch_base is None and te > now + 60:        # clock-derived base rolled over since the event
            te -= 1e5
        o = {"shot": a.shot, "take": a.take, "step": int(s), "action": act, "t_epoch": round(te, 2)}
        if bb:
            o["bbox"] = [round(float(x), 1) for x in bb.split(",")]   # fractional CSS px (real logs: 221.9) - int("221.9") raises
        if act == "readback":
            o["value"] = v.rstrip(OK + BAD)
            o["ok"] = v.endswith(OK)
        elif v:
            o["value"] = v
        if sel:
            o["selector"] = sel
        f.write(json.dumps(o, ensure_ascii=False) + "\n")
        n += 1
print("ingested", n, "->", log)
