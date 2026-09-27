"""Test các sửa của lượt nghiệm thu Opus stand-in 27/09 (crop_top_measured, viewport_origin, build chặn).
Chạy: python scripts/capture/tests/test_review_fixes.py"""
import json, pathlib, sys, tempfile
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

tmp = pathlib.Path(tempfile.mkdtemp())
wd = tmp / "wd.md"; wd.write_text("899.000", encoding="utf-8")
base = {"capture": {"dpr": 1.25, "viewport_css": [1536, 730], "crop_top": 70, "viewport_origin_px": [0, 70], "crop_top_measured": False},
        "global_avoid": [{"selector": "text=x", "reason": "r"}],
        "shots": [{"id": "s1", "vo_line": "v", "duration_target": 3, "url": "/a", "preconditions": ["p"], "camera": [], "highlight": [],
                   "cursor": [], "expected_on_screen": ["899.000"], "avoid": [], "9x16_focus": "text=a",
                   "steps": [{"action": "hover", "selector": "text=a"}]}]}
err, warn, _ = C.lint(base, str(wd))
check("crop_top_measured false -> WARN (G0 vẫn PASS)", not err and any("crop_top_measured" in w for w in warn))
m = json.loads(json.dumps(base)); m["capture"]["crop_top_measured"] = True
err, warn, _ = C.lint(m, str(wd)); check("crop_top_measured true -> không WARN", not any("crop_top_measured" in w for w in warn))
b = json.loads(json.dumps(base)); b["capture"]["viewport_origin_px"] = [0, 0]
err, _, _ = C.lint(b, str(wd)); check("viewport_origin_px ≠ [0, crop_top] -> FAIL", any("viewport_origin_px" in e for e in err))
sp = tmp / "s.json"; sp.write_text(json.dumps(base), encoding="utf-8")
lg = tmp / "log.jsonl"; lg.write_text(json.dumps({"event": "rec_start", "shot": "s1", "t_epoch": 1.0}) + "\n", encoding="utf-8")
rc = C.main(["build", "--script", str(sp), "--log", str(lg), "--out", str(tmp / "o")])
check("build CLI từ chối khi chưa đo (exit 2)", rc == 2)
rc = C.main(["build", "--script", str(sp), "--log", str(lg), "--out", str(tmp / "o"), "--allow-unmeasured"])
check("build --allow-unmeasured chạy (exit 0)", rc == 0)
print(f"PASS {ok}/5")
