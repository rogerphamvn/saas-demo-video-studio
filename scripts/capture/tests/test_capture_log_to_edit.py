"""Small test for capture_log_to_edit.py with a FAKE capture log (no browser, no ffmpeg).

  python scripts/capture/tests/test_capture_log_to_edit.py      -> prints PASS n/n, exit 1 on failure
"""
import json
import pathlib
import sys
import tempfile

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # capture/capture_log_to_edit.py
import capture_log_to_edit as C  # noqa: E402
assert "rec_start" in C.ACTIONS, C.__file__  # v3 build of the script

REC = 1790394936.6
SCRIPT = {
    "web_data": "WD",
    "capture": {"browser_zoom": 100, "dpr": 1.25, "viewport_css": [1536, 808], "viewport_origin_px": [0, 70],
                "crop": "crop=1920:1010:0:70", "max_zoom": 1.5},
    "forbidden_pages": ["/admin"],
    "global_avoid": [{"selector": ".user-email", "reason": "email"}],
    "never_click": ["text=Lưu"],
    "shots": [{
        "id": "s01", "vo_line": "Lô hàng này lãi hay lỗ?", "duration_target": 5, "url": "/batches/1/edit",
        "preconditions": ["trang có dữ liệu"],
        "steps": [{"action": "click", "selector": "#price"}, {"action": "type", "selector": "#price", "value": "899000"},
                  {"action": "hover", "selector": "#net"}],
        "camera": [{"t_rel": 0.0, "zoom_to": "#price", "level": 2.0, "zoom_out_at": 3.0}],
        "highlight": [{"selector": "#net", "kind": "callout", "text": "8.879.840", "t_rel": 1.0, "dur": 1.5}],
        "cursor": ["#price", "#net"], "expected_on_screen": ["899.000", "8.879.840"], "avoid": [], "9x16_focus": "#net"}],
}


def row(step, action, sel, t, x, y, w, h):
    return {"shot": "s01", "step": step, "action": action, "t_epoch": REC + t, "selector": sel,
            "bbox": {"x": x, "y": y, "w": w, "h": h}, "viewport": {"w": 1536, "h": 808}, "dpr": 1.25, "scrollY": 0}


def run():
    res = []
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        wd = td / "web-data.md"
        wd.write_text("Giá 899.000 · Net 8.879.840 (32.92%)", encoding="utf-8")
        sc = json.loads(json.dumps(SCRIPT))
        sc["web_data"] = str(wd)
        # --- lint: clean script except camera level 2.0 > 1.5 -> exactly that error
        err, _, total = C.lint(sc, None)
        res.append(("lint flags level>1.5 only", len(err) == 1 and "level 2.0" in err[0] and total == 5))
        bad = json.loads(json.dumps(sc))
        bad["shots"][0]["camera"][0]["level"] = 1.4
        bad["shots"][0]["expected_on_screen"].append("909%")
        bad["shots"][0]["steps"].append({"action": "click", "selector": "text=Lưu"})
        bad["shots"][0]["url"] = "/admin/users"
        err, _, _ = C.lint(bad, None)
        res.append(("lint catches 909% / Lưu / forbidden page", len(err) == 3))
        ok = json.loads(json.dumps(bad))
        ok["shots"][0]["expected_on_screen"].pop(); ok["shots"][0]["steps"].pop(); ok["shots"][0]["url"] = "/batches/1/edit"
        res.append(("lint PASS on fixed script", C.lint(ok, None)[0] == []))
        # --- build from a fake log
        log = td / "capture-log.jsonl"
        rows = [{"event": "rec_start", "t_epoch": REC},
                row(0, "click", "#price", 10.0, 300, 236, 180, 34),
                row(1, "type", "#price", 10.5, 300, 236, 180, 34),
                row(2, "hover", "#net", 12.0, 1100, 180, 200, 40),
                row("m", "measure", ".user-email", 10.0, 1400, 10, 120, 20)]
        log.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
        out = td / "data"
        (td / "s.json").write_text(json.dumps(ok), encoding="utf-8")
        rc = C.main(["build", "--script", str(td / "s.json"), "--log", str(log), "--out", str(out)])
        cur = json.loads((out / "cursor-path.json").read_text(encoding="utf-8"))
        cam = json.loads((out / "camera-cues.json").read_text(encoding="utf-8"))
        hl = json.loads((out / "highlight-cues.json").read_text(encoding="utf-8"))
        pv = json.loads((out / "privacy-boxes.json").read_text(encoding="utf-8"))
        res.append(("build rc 0", rc == 0))
        # CSS (300,236,180,34) x1.25, origin 70 - crop 70 -> footage (375,295,225,42.5), centre (487.5,316.2)
        clk = [c for c in cur if c["act"] == "click"]
        res.append(("click at bbox centre in footage px", len(clk) == 1 and clk[0]["x"] == 487.5 and clk[0]["y"] == 316.2
                    and abs(clk[0]["t_src"] - 10.0) < 1e-3))
        res.append(("move arrives 0.15 s before click", any(c["act"] == "move" and abs(c["t_src"] - 9.85) < 1e-3 for c in cur)))
        res.append(("type on same field adds no extra point", len(cur) == 3))
        # camera: level 1.4 (fixed script) at the price box, clamped to frame edge (half window 1920/2.8=685.7, 1010/2.8=360.7)
        z = cam[0]
        res.append(("camera clamp to edges", z["scale"] == 1.4 and z["fx"] == 685.7 and z["fy"] == 360.7))
        res.append(("zoom_out cue 1.0x at t_rel 3", len(cam) == 2 and cam[1]["scale"] == 1.0 and abs(cam[1]["t_src"] - 13.0) < 1e-3))
        res.append(("highlight box in footage px", hl[0]["box"] == [1375.0, 225.0, 250.0, 50.0] and hl[0]["text"] == "8.879.840"))
        res.append(("privacy box from global_avoid", len(pv) == 1 and pv[0]["box"] == [1750.0, 12.5, 150.0, 25.0]))
        # camera over-zoom is capped even when the script asks 2.0
        g = C.Geo(SCRIPT["capture"])
        res.append(("hard cap 1.5x", g.camera([375, 295, 225, 42.5], 2.0)[2] == 1.5))
        # footage.json mapping -> film time + scene selector
        fj = td / "footage.json"
        fj.write_text(json.dumps({"clips": [{"id": "s01", "sel": "#sc01 .footage", "start": 2.0, "src_in": 9.5, "src_out": 15.0}]}),
                      encoding="utf-8")
        C.main(["build", "--script", str(td / "s.json"), "--log", str(log), "--footage", str(fj), "--out", str(out)])
        cur2 = json.loads((out / "cursor-path.json").read_text(encoding="utf-8"))
        c2 = [c for c in cur2 if c["act"] == "click"][0]
        res.append(("footage.json -> film t + scene", c2["scene"] == "#sc01" and abs(c2["t"] - 2.5) < 1e-3))
        # --- draft from a feature map (RECON) -> lint clean
        fm = {"app": "Demo", "app_type": "form_calculator", "web_data": str(wd), "capture": SCRIPT["capture"],
              "never_click": ["text=Lưu"], "global_avoid": SCRIPT["global_avoid"],
              "routes": [
                  {"route": "/compare", "type": "dashboard", "data_ok": True, "beat": "proof",
                   "trigger": {"action": "click", "selector": "text=Batch B"},
                   "wow_element": {"selector": "text=nhỉnh hơn", "number": "32.92%"}},
                  {"route": "/batches/1/edit", "data_ok": True, "beat": "hook",
                   "trigger": {"action": "type", "selector": "#price", "fallback_text": "Giá bán", "value": "899000"},
                   "wow_element": {"selector": "#net", "number": "8.879.840"}},
                  {"route": "/marketing", "data_ok": False, "empty_reason": "empty state"}]}
        d = C.draft(fm)
        sh = d["shots"]
        res.append(("draft orders beats hook→proof, 1 shot/beat", [s["id"] for s in sh] == ["s01-hook", "s02-proof"]))
        res.append(("draft recipe by type (form: click+type · dashboard)",
                    [st["action"] for st in sh[0]["steps"]] == ["navigate", "click", "type", "hold"] and sh[1]["app_type"] == "dashboard"
                    and sh[0]["steps"][1].get("fallback_text") == "Giá bán"))
        err, _, _ = C.lint(d, None)
        res.append(("unfilled draft FAILS G0 (placeholders)", len(err) == 2 and all("nháp chưa điền" in e for e in err)))
        for s_ in d["shots"]:
            s_["vo_line"], s_["anchor_word"] = "Câu VO thật.", "thật"
        res.append(("filled draft passes G0 lint", C.lint(d, None)[0] == []))
        bad_fm = json.loads(json.dumps(fm))
        bad_fm["routes"][2]["beat"] = "feature1"
        try:
            C.draft(bad_fm)
            res.append(("draft refuses beat on data_ok:false route", False))
        except SystemExit:
            res.append(("draft refuses beat on data_ok:false route", True))
        # brittle selector warning + not-found log line reported
        br = json.loads(json.dumps(ok))
        br["shots"][0]["steps"].append({"action": "hover", "selector": "div > div > div > span:nth-child(3)"})
        res.append(("lint warns brittle selector", any("giòn" in w for w in C.lint(br, None)[1])))
        log.write_text(log.read_text(encoding="utf-8") + "\n" + json.dumps({"shot": "s01", "selector": "#gone", "error": "not found",
                                                                             "t_epoch": REC + 13}), encoding="utf-8")
        rep = C.build(ok, C.load_log(log), REC, None, out)
        res.append(("build reports selector not found", any("#gone" in n for n in rep["notes"])))
        res.append(("snippet has fallback + selector_used", "FALLBACK_TEXT" in C.JS_SNIPPET and "selector_used" in C.JS_SNIPPET))
    for name, ok_ in res:
        print(("PASS " if ok_ else "FAIL ") + name)
    n = sum(1 for _, o in res if o)
    print(f"PASS {n}/{len(res)}" if n == len(res) else f"FAIL {n}/{len(res)}")
    return 0 if n == len(res) else 1


if __name__ == "__main__":
    sys.exit(run())
