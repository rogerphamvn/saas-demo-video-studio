"""Test phần VÁ v3 của capture_log_to_edit.py (bản sao, 27/09/2026). Chạy: python scripts/capture/tests/test_v3_patch.py"""
import json, pathlib, sys, tempfile, types
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # capture/capture_log_to_edit.py
import capture_log_to_edit as C  # noqa: E402

ok = 0
def check(name, cond):
    global ok
    print(("PASS " if cond else "FAIL ") + name); ok += bool(cond)
    if not cond: sys.exit(1)

wd = pathlib.Path(tempfile.mkdtemp()) / "wd.md"; wd.write_text("899.000 717.200", encoding="utf-8")
base = {"capture": {"dpr": 1.25, "viewport_css": [1536, 808], "crop_top": 70, "viewport_origin_px": [0, 70], "max_zoom": 1.5},
        "global_avoid": [{"selector": "text=x", "reason": "r"}], "never_click": ["text=Xóa"],
        "shots": [{"id": "s1", "vo_line": "v", "duration_target": 3, "url": "/a", "preconditions": ["p"], "camera": [], "highlight": [],
                   "cursor": [], "expected_on_screen": ["899.000"], "avoid": [], "9x16_focus": "text=a",
                   "steps": [{"action": "zoom", "selector": "text=a", "level": 1.8}, {"action": "select", "selector": "text=b", "value": "Giảm %"},
                             {"action": "zoom_out"}, {"action": "rec_stop"}]}]}
err, warn, _ = C.lint(base, str(wd)); check("crop_top thay crop + zoom 1.8 + select hợp lệ -> G0 PASS", not err)
bad = json.loads(json.dumps(base)); bad["shots"][0]["steps"][0]["level"] = 2.4
err, _, _ = C.lint(bad, str(wd)); check("zoom tại nguồn 2.4 > 2.0 -> FAIL", any("zoom tại nguồn" in e for e in err))
bad2 = json.loads(json.dumps(base)); del bad2["capture"]["crop_top"]
err, _, _ = C.lint(bad2, str(wd)); check("thiếu cả crop lẫn crop_top -> FAIL", any("crop_top" in e for e in err))
g = C.Geo(base["capture"]); check("Geo crop_top: footage 1920x1010, y triệt tiêu 70", (g.fw, g.fh, g.cy) == (1920, 1010, 70)
      and g.box({"bbox": {"x": 100, "y": 100, "w": 10, "h": 10}, "dpr": 1.25})[1] == 125.0)
rows = [{"event": "rec_start", "shot": "s1", "t_epoch": 1000.0},
        {"shot": "s1", "step": 0, "action": "zoom", "level": 1.8, "t_epoch": 1002.0, "selector": "text=a", "bbox": {"x": 0, "y": 0, "w": 10, "h": 10}},
        {"shot": "s1", "step": 1, "action": "click", "t_epoch": 1003.0, "selector": "text=b", "bbox": {"x": 100, "y": 100, "w": 20, "h": 20}}]
a = types.SimpleNamespace(rec_start=None, markers=None)
per = C.rec_starts_per_shot(a, rows); check("rec_start theo shot đọc từ log", per == {"s1": 1000.0})
out = pathlib.Path(tempfile.mkdtemp())
res = C.build(base, rows, C.rec_start_from(a, rows), None, out, per)
cam = json.loads((out / "camera-cues.json").read_text(encoding="utf-8"))
cur = json.loads((out / "cursor-path.json").read_text(encoding="utf-8"))
check("zoom tại nguồn ghi vào camera-cues (source_zoom 1.8, t_src 2.0)", cam and cam[0].get("source_zoom") == 1.8 and cam[0]["t_src"] == 2.0)
check("click t_src tính từ rec_start CỦA shot (3.0)", any(c["act"] == "click" and c["t_src"] == 3.0 for c in cur))
print(f"PASS {ok}/7")

# VÒNG 2 (27/09): rec_start + shows_old_lots + expect_value
r2 = json.loads(json.dumps(base)); r2["shots"][0]["steps"] = [
    {"action": "select", "selector": "text=A", "value": "Demo", "shows_old_lots": True},
    {"action": "rec_start"}, {"action": "type", "selector": "text=B", "value": "1", "expect_value": "1"}, {"action": "rec_stop"}]
err, warn, _ = C.lint(r2, str(wd)); check("select lô cũ TRƯỚC rec_start -> PASS, không warn expect_value", not err and not any("expect_value" in w for w in warn))
r3 = json.loads(json.dumps(r2)); r3["shots"][0]["steps"].insert(2, {"action": "select", "selector": "text=A", "value": "x", "shows_old_lots": True})
err, _, _ = C.lint(r3, str(wd)); check("select lô cũ TRONG khoảng ghi -> FAIL", any("shows_old_lots" in e for e in err))
r4 = json.loads(json.dumps(r2)); del r4["shots"][0]["steps"][2]["expect_value"]
_, warn, _ = C.lint(r4, str(wd)); check("type thiếu expect_value -> WARN", any("expect_value" in w for w in warn))
print(f"PASS {ok}/10")
