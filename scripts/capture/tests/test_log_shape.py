"""Test the 28/09 fixes of capture_log_to_edit.py build: bbox as a LIST [x,y,w,h] (shape of the real 27/09 macro log),
several takes of one shot in the same log, per-file rec_start written by rec.py as `rec_start <epoch> <shot>_<take>`.
Run: python scripts/capture/tests/test_log_shape.py"""
import json
import pathlib
import sys
import tempfile

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import capture_log_to_edit as C  # noqa: E402

ok = 0
res = []


def check(name, cond):
    global ok
    res.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name)
    ok += bool(cond)


tmp = pathlib.Path(tempfile.mkdtemp())
sc = {"capture": {"dpr": 1, "viewport_css": [1920, 1010], "crop_top": 70, "viewport_origin_px": [0, 70], "crop_top_measured": True},
      "global_avoid": [{"selector": "text=x", "reason": "r"}],
      "shots": [{"id": "R01", "vo_line": "v", "duration_target": 3, "url": "/a", "preconditions": ["p"], "camera": [], "highlight": [],
                 "cursor": [], "expected_on_screen": ["1"], "avoid": [], "9x16_focus": "text=a",
                 "steps": [{"action": "click", "selector": "text=a"}]}]}
rows = [{"shot": "R01", "take": "t1", "step": 1, "action": "click", "selector": "text=a", "t_epoch": 1000.0, "bbox": [100, 200, 20, 10]},
        {"shot": "R01", "take": "t5", "step": 1, "action": "click", "selector": "text=a", "t_epoch": 5003.0, "bbox": [300, 400, 20, 10]}]
mk = tmp / "markers.txt"
mk.write_text("rec_start 990.0 R01_t1\nrec_stop 1100.0 R01_t1\nrec_start 5000.0 R01_t5\nrec_stop 5100.0 R01_t5\n", encoding="utf-8")


class A:
    rec_start = None
    markers = str(mk)


per = C.rec_starts_per_shot(A, rows)
check("markers <shot>_<take> read", per == {"R01_t1": 990.0, "R01_t5": 5000.0})
out = tmp / "o"
rep = C.build(sc, rows, C.rec_start_from(A, rows), None, out, per)
cur = json.loads((out / "cursor-path.json").read_text(encoding="utf-8"))
clk = [c for c in cur if c["act"] == "click"]
check("list bbox accepted, last take (t5) used by default", len(clk) == 1 and clk[0]["x"] == 310.0 and clk[0]["y"] == 405.0)
check("t_src from the t5 file start (3.0 s)", abs(clk[0]["t_src"] - 3.0) < 1e-6)
check("note says which take was used", any("t5" in n and "take" in n for n in rep["notes"]))
rep2 = C.build(sc, rows, C.rec_start_from(A, rows), None, out, per, {"R01": "t1"})
cur2 = json.loads((out / "cursor-path.json").read_text(encoding="utf-8"))
c2 = [c for c in cur2 if c["act"] == "click"][0]
check("--takes R01=t1 picks t1 (t_src 10.0 from its own rec_start)", c2["x"] == 110.0 and abs(c2["t_src"] - 10.0) < 1e-6)
n = sum(1 for _, o in res if o)
print(f"PASS {n}/{len(res)}" if n == len(res) else f"FAIL {n}/{len(res)}")
sys.exit(0 if n == len(res) else 1)
