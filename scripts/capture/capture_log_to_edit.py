"""Capture script (kịch bản quay) + capture log  ->  cursor / camera / highlight cues in FOOTAGE px.

STATUS: SMOKE-TESTED - v3 of 27/09 (source zoom, per-file rec_start, crop_top, select/slider/key/inject/rec_stop).
        `lint` ran for real on 27/09 (G0 PASS on the ProfitBase script); draft/snippet are covered by tests only.
        `build` was NOT run on 27/09 and CRASHED on the real 27/09 log (bbox logged as a list [x,y,w,h], code read
        bbox["x"]; 2 off-camera rows had no t_epoch). Fixed here: Geo.box accepts list or dict; rows without t_epoch are
        reported and skipped; one take per shot (log rows carry "take": the shot's
        `take:` field, else --takes, else the LAST take in the log); per-file rec_start looked up as <shot>_<take>
        (rec.py writes `rec_start <epoch> <shot>_<take>`). Re-run on a copy of the real log + capture/tests/.

Why (ProfitBase 26/09/2026): the recording had only per-scene time markers, so the edit had to find the pointer by colour
(track_pointer.py), guess zoom regions, split a scene into 3 pieces to fit the VO, drop empty pages, mask an old chat...
With a capture script + a log of getBoundingClientRect() at every action, the edit data comes straight from the DOM.

Sub-commands (guide + per-app-type recipes: see the repo docs on the capture script):

  draft  = feature-map.yaml (RECON result) -> draft capture script, one shot per story beat, recipe by app_type
      python scripts/capture/capture_log_to_edit.py draft --feature-map feature-map.yaml --out capture-script.draft.yaml

  snippet = print the browser JS that returns one capture-log line for a selector

  lint   = gate G0 BEFORE recording: required fields, zoom <= max, every expected_on_screen found in web-data,
           no forbidden page, no click on a never_click selector (Save/Delete), highlight text is a real number.
      python scripts/capture/capture_log_to_edit.py lint --script capture-script.yaml --web-data footage/web-data-2026-09-26.md

  build  = AFTER recording: read the capture log and write
           <out>/cursor-path.json     same entry shape as window.CURSOR in the skeleton ({scene, clip, t, x, y, act})
           <out>/camera-cues.json     [{shot, t, fx, fy, scale<=max_zoom, ease, dur, box}]  (fx, fy = footage point to centre)
           <out>/highlight-cues.json  [{shot, t, dur, kind, text, box:[x,y,w,h]}]
           <out>/privacy-boxes.json   [{shot, t, box, reason}]  from `avoid` / `global_avoid` selectors that were logged
      python scripts/capture/capture_log_to_edit.py build --script capture-script.yaml --log footage/capture-log.jsonl \
             --markers footage/markers.txt [--footage data/footage.json] --out data/

Capture log = JSON Lines, one object per logged step (written by the browser agent while recording):
  {"shot":"s01-hook","step":2,"action":"click","t_epoch":1790394946.12,"selector":"input[name=price]",
   "bbox":{"x":300,"y":236,"w":180,"h":34},"viewport":{"w":1536,"h":808},"dpr":1.25,"scrollY":0}
  - bbox = el.getBoundingClientRect() in CSS px, relative to the viewport, taken AT the moment of the action.
    `python scripts/capture/capture_log_to_edit.py snippet` prints the browser JS (Claude-in-Chrome javascript_tool): it resolves
    text= / aria= / testid= / role= / CSS selectors, falls back to fallback_text, returns the JSON (+ selector_used).
    Add shot / step / action / selector (the SCRIPT's selector) to that object and append it; log BEFORE a click that
    navigates away. {"error":"not found"} lines are reported by build.
  - action "measure" = bbox of a camera/highlight/avoid selector (not an interaction).
  - {"event":"rec_start","t_epoch":...} line, or --markers file with a `rec_start <epoch>` line, or --rec-start.
  Browser Date.now()/1000 and Python time.time() read the same OS clock, so t_epoch and ffmpeg markers line up.

Coordinates:  footage_x = css_x * dpr + viewport_origin_x - crop_x      (same for y)
  capture.viewport_origin_px = where the viewport's top-left sits on the physical screen (70 px under the yellow
  "Claude is debugging this browser" bar); capture.crop = the crop applied to the footage ("crop=1920:1010:0:70").
  With that bar present both are 70, so they cancel: footage_y = css_y * dpr. Check 1-2 boxes on a real frame anyway.

Time: t_src = t_epoch - rec_start (seconds in the raw capture). With --footage (data/footage.json written by
  cut_clips.py) each cue is also mapped to film time `t` + scene selector; without it `t` = t_src ("time_base":"src").

Only stdlib (+ PyYAML if the script is .yaml; a .json capture script needs nothing).
"""
import argparse
import json
import pathlib
import re
import sys

ACTIONS = {"navigate", "scroll_to", "hover", "click", "type", "wait", "hold", "drag",   # drag: selector -> value (target selector)
           "zoom", "zoom_out", "select", "slider", "key", "inject", "rec_stop", "rec_start"}  # rec_start: vòng 2          # PATCH v3 (ProfitBase 27/09): zoom TẠI NGUỒN, dropdown, slider, phím, tiêm CSS, dừng ghi
SOURCE_ZOOM_MAX = 2.0   # PATCH v3: zoom TẠI NGUỒN (CSS transform lúc quay, Chrome vẽ lại chữ nét) được tới 2.0×; camera hậu kỳ vẫn ≤ 1.5×
NEEDS_SELECTOR = {"scroll_to", "hover", "click", "type", "drag", "zoom", "select", "slider"}
HL_KINDS = {"spotlight", "underline", "box", "callout"}
SHOT_FIELDS = ["id", "vo_line", "duration_target", "url", "preconditions", "steps", "camera", "highlight", "cursor",
               "expected_on_screen", "avoid", "9x16_focus"]
HARD_MAX_ZOOM = 1.5
BRITTLE = re.compile(r"^xy=|nth-child|nth-of-type|\.css-[0-9a-z]{4,}|\.[a-z]+-[0-9a-f]{5,}|(\s*>\s*.*){3,}")

JS_SNIPPET = r"""(function (sel, fallback) {
  const txt = (e) => (e.innerText || e.getAttribute("aria-label") || "").trim();
  const byText = (t) => { const m = [...document.querySelectorAll("body *")].filter((e) => e.offsetParent && txt(e).includes(t));
    return m.find((e) => ![...e.children].some((c) => m.includes(c))) || null; };        // deepest element holding the text
  const find = (s) => {
    if (!s) return null;
    if (s.startsWith("text=")) return byText(s.slice(5));
    if (s.startsWith("aria=")) return document.querySelector(`[aria-label="${s.slice(5)}"]`);
    if (s.startsWith("testid=")) return document.querySelector(`[data-testid="${s.slice(7)}"]`);
    if (s.startsWith("role=")) { const [r, n] = s.slice(5).split(":");
      return [...document.querySelectorAll(`[role="${r}"],${r}`)].find((e) => !n || txt(e).includes(n)) || null; }
    try { return document.querySelector(s); } catch (e) { return null; } };
  let el = find(sel), used = sel;
  if (!el && fallback) { el = byText(fallback); used = "text=" + fallback; }
  if (!el) return JSON.stringify({ error: "not found", selector: sel, t_epoch: Date.now() / 1000 });
  const r = el.getBoundingClientRect();
  return JSON.stringify({ t_epoch: Date.now() / 1000, selector_used: used, bbox: { x: r.x, y: r.y, w: r.width, h: r.height },
    viewport: { w: innerWidth, h: innerHeight }, dpr: devicePixelRatio, scrollY: scrollY });
})("SELECTOR", "FALLBACK_TEXT")"""

DRAFT_MARKERS = ["<VIẾT", "<GIÁ TRỊ CHỐT>", "<từ neo>", "<selector đích>"]   # left by `draft`; lint fails until filled
BEATS = ["hook","problem", "feature1", "feature2", "feature3", "proof", "cta"]


# ------------------------------------------------------------------ io
def load_script(path):
    p = pathlib.Path(path)
    txt = p.read_text(encoding="utf-8")
    if p.suffix.lower() in (".yaml", ".yml"):
        try:
            import yaml  # noqa: PLC0415
        except ImportError:
            sys.exit("PyYAML chưa cài: `pip install pyyaml`, hoặc lưu kịch bản dạng .json")
        return yaml.safe_load(txt)
    return json.loads(txt)


def load_log(path):
    rows = []
    for n, line in enumerate(pathlib.Path(path).read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as e:
            sys.exit(f"capture log dòng {n}: JSON lỗi ({e})")
    return rows


def rec_starts_per_shot(args, rows):
    """PATCH v3: 1 file/shot => mỗi shot có rec_start riêng. Nguồn: log {"event":"rec_start","shot":id,"t_epoch":..}
    hoặc markers.txt dòng `rec_start <epoch> <shot>`. Trả {shot: epoch}; shot không có => dùng rec_start chung."""
    out = {}
    for r in rows:
        if r.get("event") == "rec_start" and r.get("shot"):
            out[r["shot"] + (f"_{r['take']}" if r.get("take") else "")] = float(r["t_epoch"])
    if getattr(args, "markers", None):
        for line in pathlib.Path(args.markers).read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) >= 3 and parts[0] == "rec_start":
                out[parts[2]] = float(parts[1])
    return out


def rec_start_from(args, rows):
    if args.rec_start is not None:
        return args.rec_start
    for r in rows:
        if r.get("event") == "rec_start" and not r.get("shot"):
            return float(r["t_epoch"])
    per = rec_starts_per_shot(args, rows)
    if per:
        return min(per.values())
    for r in rows:
        if r.get("event") == "rec_start":
            return float(r["t_epoch"])
    if args.markers:
        for line in pathlib.Path(args.markers).read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[0] == "rec_start":
                return float(parts[1])
    sys.exit("thiếu rec_start: thêm dòng {\"event\":\"rec_start\",...} vào log, hoặc --markers, hoặc --rec-start")


def norm(s):
    return re.sub(r"\s+", "", str(s)).lower()


# ------------------------------------------------------------------ lint (gate G0)
def lint(sc, web_data_path):
    err, warn = [], []
    cap = sc.get("capture", {})
    max_zoom = min(float(cap.get("max_zoom", HARD_MAX_ZOOM)), HARD_MAX_ZOOM)
    for k in ("dpr", "viewport_css"):
        if k not in cap:
            err.append(f"capture.{k} thiếu (đo trước khi quay)")
    if "crop" not in cap and "crop_top" not in cap:          # PATCH v3: gfxcapture theo HWND dùng crop_top (px vật lý)
        err.append("capture.crop hoặc capture.crop_top thiếu (đo P9 trước khi quay)")
    if "crop_top" in cap:                                     # REVIEW 27/09 (Opus stand-in): cờ đo P9 + bất biến origin
        if cap.get("crop_top_measured") is not True:
            warn.append("capture.crop_top_measured != true — crop_top/viewport_css/dpr là PLACEHOLDER; "
                        "`build` sẽ TỪ CHỐI chạy tới khi P9 đo trên khung gfxcapture thật và đổi cờ thành true")
        vo = cap.get("viewport_origin_px")
        if vo is not None and list(vo) != [0, cap["crop_top"]]:
            err.append(f"capture.viewport_origin_px {vo} ≠ [0, crop_top={cap['crop_top']}] — toạ độ footage sẽ lệch")
    src_max = float(cap.get("max_source_zoom", SOURCE_ZOOM_MAX))
    if cap.get("browser_zoom", 100) != 100:
        err.append(f"capture.browser_zoom = {cap.get('browser_zoom')} — phải 100")
    wd_path = web_data_path or sc.get("web_data")
    wd = ""
    if not wd_path or not pathlib.Path(wd_path).exists():
        err.append(f"web-data không đọc được ({wd_path}) — soát dữ liệu (bước 2) TRƯỚC khi viết kịch bản")
    else:
        wd = norm(pathlib.Path(wd_path).read_text(encoding="utf-8"))
    forbidden = sc.get("forbidden_pages", [])
    never = [norm(x) for x in sc.get("never_click", [])]
    if not sc.get("global_avoid"):
        warn.append("global_avoid rỗng — kiểm privacy-checklist (email, role/ADMIN, vendor AI)")
    ids, total = set(), 0.0
    for i, s in enumerate(sc.get("shots", [])):
        sid = s.get("id", f"#{i}")
        if sid in ids:
            err.append(f"{sid}: id trùng")
        ids.add(sid)
        if s.get("capture") is False:          # shot not recorded (card / montage over a still) - reason required
            if not s.get("replace_with"):
                err.append(f"{sid}: capture:false nhưng thiếu replace_with (thay bằng gì?)")
            total += float(s.get("duration_target", 0) or 0)
            continue
        for f in SHOT_FIELDS:
            if f not in s:
                err.append(f"{sid}: thiếu trường `{f}`")
        left = [m for m in DRAFT_MARKERS if m in json.dumps(s, ensure_ascii=False)]
        if left:
            err.append(f"{sid}: nháp chưa điền xong ({', '.join(left)})")
        total += float(s.get("duration_target", 0) or 0)
        url = str(s.get("url", ""))
        if any(url.startswith(fp) for fp in forbidden):
            err.append(f"{sid}: url {url} nằm trong forbidden_pages")
        if not s.get("preconditions"):
            err.append(f"{sid}: preconditions rỗng")
        exp = s.get("expected_on_screen") or []
        if not exp:
            err.append(f"{sid}: expected_on_screen rỗng — trang không có số/chữ để kiểm = nghi trang TRỐNG")
        for v in exp:
            if wd and norm(v) not in wd:
                err.append(f"{sid}: expected_on_screen '{v}' KHÔNG có trong web-data")
        steps = s.get("steps") or []
        if not steps:
            err.append(f"{sid}: steps rỗng")
        recording = not any(x.get("action") == "rec_start" for x in steps)   # VÒNG 2: có rec_start => bước trước nó là OFF-CAMERA
        for j, st in enumerate(steps):
            if st.get("action") == "rec_start":
                recording = True
            elif st.get("action") == "rec_stop":
                recording = False
            if recording and st.get("shows_old_lots"):
                err.append(f"{sid}.steps[{j}]: bước mở danh sách có lô CŨ (shows_old_lots) nằm TRONG khoảng ghi hình — làm OFF-CAMERA trước rec_start")
            if st.get("action") == "type" and "expect_value" not in st:
                warn.append(f"{sid}.steps[{j}]: type thiếu expect_value (log giá trị ô sau khi gõ)")
            a = st.get("action")
            if a not in ACTIONS:
                err.append(f"{sid}.steps[{j}]: action '{a}' không hợp lệ ({sorted(ACTIONS)})")
            if a in NEEDS_SELECTOR and not st.get("selector"):
                err.append(f"{sid}.steps[{j}]: {a} cần selector")
            if a in ("navigate", "type") and st.get("value") in (None, ""):
                err.append(f"{sid}.steps[{j}]: {a} cần value")
            if a == "navigate" and any(str(st.get("value", "")).startswith(fp) for fp in forbidden):
                err.append(f"{sid}.steps[{j}]: navigate tới trang cấm {st.get('value')}")
            if st.get("selector") and BRITTLE.search(str(st["selector"])) and not st.get("fallback_text"):
                warn.append(f"{sid}.steps[{j}]: selector giòn '{st['selector']}' — thêm fallback_text hoặc dùng text=/aria=/testid=")
            if a in ("select", "slider", "key") and st.get("value") in (None, ""):
                err.append(f"{sid}.steps[{j}]: {a} cần value")
            if a == "zoom" and float(st.get("level", 0) or 0) > min(src_max, SOURCE_ZOOM_MAX):
                err.append(f"{sid}.steps[{j}]: zoom tại nguồn level {st.get('level')} > {min(src_max, SOURCE_ZOOM_MAX)}")
            if a == "zoom" and not st.get("level"):
                err.append(f"{sid}.steps[{j}]: zoom cần level")
            if a == "drag" and not st.get("value"):
                err.append(f"{sid}.steps[{j}]: drag cần value = selector đích")
            if a in ("click", "type") and norm(st.get("selector", "")) in never:
                err.append(f"{sid}.steps[{j}]: {a} vào selector cấm bấm '{st.get('selector')}' (never_click)")
        for j, c in enumerate(s.get("camera") or []):
            if not c.get("zoom_to"):
                err.append(f"{sid}.camera[{j}]: thiếu zoom_to")
            if float(c.get("level", 1.0)) > max_zoom:
                err.append(f"{sid}.camera[{j}]: level {c.get('level')} > {max_zoom} (footage mềm chữ)")
        for j, h in enumerate(s.get("highlight") or []):
            if h.get("kind") not in HL_KINDS:
                err.append(f"{sid}.highlight[{j}]: kind '{h.get('kind')}' không hợp lệ ({sorted(HL_KINDS)})")
            if not h.get("selector"):
                err.append(f"{sid}.highlight[{j}]: thiếu selector")
            t = h.get("text")
            if t and wd and norm(t) not in wd:
                err.append(f"{sid}.highlight[{j}]: text '{t}' không có trong web-data (chỉ số THẬT)")
        if not s.get("9x16_focus"):
            warn.append(f"{sid}: 9x16_focus trống — hero slot bản dọc sẽ không biết giữ vùng nào")
    return err, warn, total


# ------------------------------------------------------------------ draft (feature-map -> capture script)
def _sel(d):
    return {"selector": d.get("selector"), **({"fallback_text": d["fallback_text"]} if d.get("fallback_text") else {})}


def _trigger_steps(tr, type_delay):
    if not tr:
        return []
    a = tr.get("action", "click")
    if a == "type":
        return [{"action": "click", **_sel(tr)},
                {"action": "type", **_sel(tr), "value": tr.get("value", "<GIÁ TRỊ CHỐT>"), "type_delay_ms": type_delay}]
    step = {"action": a, **_sel(tr)}
    if a == "drag":
        step["value"] = tr.get("value", "<selector đích>")
    return [step]


def recipe(kind, r):
    """Shot skeleton per app type (references/capture-script-by-app-type.md §2). Returns steps, camera, highlight, pre, dur."""
    tr, wow = r.get("trigger") or {}, r.get("wow_element") or {}
    num = wow.get("number")
    nav = [{"action": "navigate", "value": r["route"], "hold_s": 0.8}]
    hl_wow = [{**_sel(wow), "kind": "callout" if num else "box", **({"text": num} if num else {}), "t_rel": 3.0, "dur": 2.0}]
    pre = ["zoom trình duyệt 100%, F11, widget/popup đã tắt", "trang có dữ liệu thật (feature-map data_ok: true)"]
    if kind == "form_calculator":
        steps = nav + _trigger_steps(tr, 150) + [{"action": "hold", "hold_s": 2.0}]
        cam = [{"t_rel": 0.8, "zoom_to": tr.get("selector"), "level": 1.5},
               {"t_rel": 3.0, "zoom_to": wow.get("selector"), "level": 1.4, "zoom_out_at": 5.5}]
        hl = [{**_sel(tr), "kind": "spotlight", "t_rel": 1.0, "dur": 1.8}] + hl_wow
        pre.append("giá trị sẽ gõ + kết quả mong đợi đã chốt (ProfitBase: 30 → 909% phải gõ lại)")
        return steps, cam, hl, pre, 6.0
    if kind == "dashboard":
        steps = nav + [{"action": "hold", "hold_s": 1.0}] + _trigger_steps(tr, 120) + [{"action": "hover", **_sel(wow), "hold_s": 2.0}]
        cam = [{"t_rel": 0.0, "zoom_to": wow.get("selector"), "level": 1.0},
               {"t_rel": 2.5, "zoom_to": wow.get("selector"), "level": 1.3, "zoom_out_at": 5.0}]
        pre.append("kỳ/bộ lọc mặc định KHÔNG trống ($0 / No data), đúng tiền tệ")
        return steps, cam, hl_wow, pre, 5.5
    if kind == "table_crud":
        steps = nav + _trigger_steps(tr, 120) + [{"action": "hold", "hold_s": 1.0}, {"action": "click", **_sel(wow)},
                                                 {"action": "hold", "hold_s": 2.0}]
        cam = [{"t_rel": 0.8, "zoom_to": tr.get("selector"), "level": 1.4},
               {"t_rel": 3.0, "zoom_to": wow.get("selector"), "level": 1.3, "zoom_out_at": 5.5}]
        pre.append("bảng KHÔNG có PII khách thật (hoặc cột đó nằm trong avoid)")
        return steps, cam, hl_wow, pre, 6.0
    if kind == "ai_chat":
        steps = nav + _trigger_steps(tr, 60) + [{"action": "wait", "hold_s": 15.0}, {"action": "scroll_to", **_sel(wow), "hold_s": 3.0}]
        cam = [{"t_rel": 0.8, "zoom_to": tr.get("selector"), "level": 1.4},
               {"t_rel": 18.0, "zoom_to": wow.get("selector"), "level": 1.5, "zoom_out_at": 21.0}]
        hl = [{**h, "t_rel": 18.3} for h in hl_wow]
        pre += ["khung chat TRỐNG (read_page: không có bong bóng cũ) — nút chat mới có thể không tạo phiên mới",
                "tên model AI ở header nằm trong global_avoid"]
        return steps, cam, hl, pre, 7.5
    if kind == "editor_canvas":
        steps = nav + [{"action": "hold", "hold_s": 0.8}] + _trigger_steps(tr, 120) + [{"action": "hold", "hold_s": 2.0}]
        cam = [{"t_rel": 0.0, "zoom_to": tr.get("selector"), "level": 1.0},
               {"t_rel": 3.0, "zoom_to": wow.get("selector"), "level": 1.3, "zoom_out_at": 5.5}]
        pre.append("tài liệu NHÁP riêng (autosave không ghi vào tài liệu của khách); đã thử kéo-thả qua extension lúc RECON")
        return steps, cam, [{**_sel(wow), "kind": "box", "t_rel": 3.0, "dur": 2.0}], pre, 6.0
    if kind == "website_landing":
        steps = nav + [{"action": "scroll_to", **_sel(wow), "hold_s": 1.5}] + \
            ([{"action": "hover", **_sel(tr), "hold_s": 1.5}] if tr else [])
        cam = [{"t_rel": 0.0, "zoom_to": wow.get("selector"), "level": 1.2, "zoom_out_at": 4.0}]
        pre.append("popup cookie/chat đã tắt (chọn từ chối); đã cuộn 1 lượt cho ảnh lazy-load tải xong")
        return steps, cam, [{**_sel(wow), "kind": "underline", **({"text": num} if num else {}), "t_rel": 0.8, "dur": 2.0}], pre, 4.5
    if kind == "multistep_flow":
        steps = nav + _trigger_steps(tr, 120) + [{"action": "hold", "hold_s": 1.5}]
        cam = [{"t_rel": 0.5, "zoom_to": tr.get("selector") or wow.get("selector"), "level": 1.3, "zoom_out_at": 3.5}]
        pre.append("dừng TRƯỚC bước gửi thật (Gửi/Đăng ký/Thanh toán)")
        return steps, cam, [{**_sel(wow), "kind": "callout", "text": num or "", "t_rel": 0.5, "dur": 2.0}], pre, 4.0
    if kind == "mobile_responsive":
        steps, cam, hl, pre2, dur = recipe("form_calculator", r)
        cam = [{**c, "level": min(c["level"], 1.3)} for c in cam]
        return steps, cam, hl, pre2 + ["viewport điện thoại (~390×844 CSS) — đo lại capture.viewport_css/dpr; dựng 9:16 native"], dur
    raise SystemExit(f"app_type '{kind}' không có công thức — dùng 1 trong: form_calculator, dashboard, table_crud, ai_chat, "
                     "editor_canvas, website_landing, multistep_flow, mobile_responsive")


def draft(fm):
    routes = [r for r in fm.get("routes", []) if r.get("beat")]
    bad = [r["route"] for r in routes if not r.get("data_ok")]
    if bad:
        raise SystemExit(f"route data_ok:false không được gán beat: {bad} (dùng capture:false + replace_with)")
    routes.sort(key=lambda r: BEATS.index(r["beat"]) if r["beat"] in BEATS else 99)
    shots = []
    for i, r in enumerate(routes, 1):
        kind = r.get("type", fm.get("app_type", "form_calculator"))
        steps, cam, hl, pre, dur = recipe(kind, r)
        wow = r.get("wow_element") or {}
        tr = r.get("trigger") or {}
        shots.append({
            "id": f"s{i:02d}-{r['beat']}", "app_type": kind,
            "vo_line": f"<VIẾT: câu VO beat {r['beat']} — {r.get('purpose', '')}>", "anchor_word": "<từ neo>",
            "duration_target": dur, "url": r["route"], "preconditions": pre, "steps": steps, "camera": cam, "highlight": hl,
            "cursor": [x for x in (tr.get("selector"), wow.get("selector")) if x],
            "expected_on_screen": [wow["number"]] if wow.get("number") else [],
            "avoid": r.get("sensitive", []), "9x16_focus": wow.get("selector") or tr.get("selector")})
    for r in fm.get("routes", []):
        if not r.get("data_ok") and r.get("beat_card"):
            shots.append({"id": f"card-{len(shots) + 1:02d}", "capture": False, "vo_line": "<VIẾT>", "duration_target": 3.0,
                          "replace_with": f"thẻ chữ trên ảnh chụp mờ {r['route']} ({r.get('empty_reason', 'trống')})"})
    keep = ("capture", "forbidden_pages", "global_avoid", "never_click", "web_data", "base_url")
    return {"project": f"{fm.get('app', '<app>')} — nháp từ feature-map", **{k: fm[k] for k in keep if k in fm}, "shots": shots}


# ------------------------------------------------------------------ geometry
def parse_crop(crop):
    m = re.match(r"crop=(\d+):(\d+):(\d+):(\d+)", crop or "")
    return tuple(int(v) for v in m.groups()) if m else None


class Geo:
    def __init__(self, cap):
        self.dpr = float(cap.get("dpr", 1.0))
        vp = cap.get("viewport_css", [1920, 1080])
        self.ox, self.oy = cap.get("viewport_origin_px", [0, 0])
        c = parse_crop(cap.get("crop"))
        if not c and cap.get("crop_top") is not None:        # PATCH v3: footage = cửa sổ HWND cắt crop_top px trên
            ct = int(cap["crop_top"]); w = round(vp[0] * self.dpr); h = round(vp[1] * self.dpr)
            c = (w, h, 0, ct)                                  # viewport_origin_px phải = [0, crop_top] để triệt tiêu
        if c:
            self.fw, self.fh, self.cx, self.cy = c
        else:
            self.fw, self.fh, self.cx, self.cy = round(vp[0] * self.dpr), round(vp[1] * self.dpr), 0, 0
        self.max_zoom = min(float(cap.get("max_zoom", HARD_MAX_ZOOM)), HARD_MAX_ZOOM)

    def box(self, row):
        b, d = row["bbox"], float(row.get("dpr", self.dpr))
        if isinstance(b, (list, tuple)):                 # macro/ingest logs write [x, y, w, h] (real 27/09 log)
            b = {"x": b[0], "y": b[1], "w": b[2], "h": b[3]}
        return [round(b["x"] * d + self.ox - self.cx, 1), round(b["y"] * d + self.oy - self.cy, 1),
                round(b["w"] * d, 1), round(b["h"] * d, 1)]

    def inside(self, bx):
        x, y, w, h = bx
        return x >= -2 and y >= -2 and x + w <= self.fw + 2 and y + h <= self.fh + 2

    def camera(self, bx, level):
        """Centre on the box, cap zoom (<= max_zoom, and so the box + 15 % margin still fits), clamp to frame edges."""
        x, y, w, h = bx
        s_fit = min(self.fw / max(w * 1.15, 1), self.fh / max(h * 1.15, 1))
        s = max(1.0, min(float(level), self.max_zoom, s_fit))
        hw, hh = self.fw / (2 * s), self.fh / (2 * s)
        fx = min(max(x + w / 2, hw), self.fw - hw)
        fy = min(max(y + h / 2, hh), self.fh - hh)
        return round(fx, 1), round(fy, 1), round(s, 3)


# ------------------------------------------------------------------ build
class Timeline:
    """Maps capture time (t_src) to film time + scene via data/footage.json (cut_clips.py manifest)."""

    def __init__(self, footage_path):
        self.clips = []
        if footage_path:
            self.clips = json.loads(pathlib.Path(footage_path).read_text(encoding="utf-8")).get("clips", [])

    def map(self, t_src, shot):
        for c in self.clips:
            if c["src_in"] <= t_src < c.get("src_out", c["src_in"] + c.get("dur", 0)):
                return {"t": round(c["start"] + (t_src - c["src_in"]), 3), "scene": c["sel"].split()[0], "clip": c["id"]}
        if self.clips:
            return None                                  # logged moment is not in any cut clip -> not on screen
        return {"t": round(t_src, 3), "scene": shot.get("scene", f"#{shot['id']}"), "clip": shot["id"], "time_base": "src"}


def build(sc, rows, rec_start, footage, out, per_shot=None, takes=None):
    per_shot = per_shot or {}
    takes = takes or {}
    geo, tl = Geo(sc.get("capture", {})), Timeline(footage)
    shots = {s["id"]: s for s in sc.get("shots", [])}
    by_shot = {}
    missing = []
    for r in rows:
        if r.get("event"):
            continue
        if r.get("error"):
            missing.append(f"{r.get('shot')}: selector '{r.get('selector')}' không tìm thấy lúc quay ({r['error']})")
            continue
        if r.get("shot") not in shots:
            print(f"WARN log shot '{r.get('shot')}' không có trong kịch bản — bỏ qua")
            continue
        if "t_epoch" not in r:                           # real 27/09 log: OFF-CAMERA steps logged without a time
            missing.append(f"{r.get('shot')}: bước {r.get('step')} ({r.get('action')}) không có t_epoch — bỏ (off-camera?)")
            continue
        by_shot.setdefault(r["shot"], []).append(r)
    notes, cursor, camera, highlight, privacy = list(missing), [], [], [], []
    take_of = {}                                          # one take per shot (several takes of a shot share the log)
    for sid_, lst in by_shot.items():
        seen_t = list(dict.fromkeys(r.get("take") for r in sorted(lst, key=lambda q: q["t_epoch"]) if r.get("take")))
        if not seen_t:
            continue
        want = shots[sid_].get("take") or takes.get(sid_) or seen_t[-1]
        if want not in seen_t:
            notes.append(f"{sid_}: take '{want}' không có trong log (có {seen_t}) — dùng {seen_t[-1]}")
            want = seen_t[-1]
        if len(seen_t) > 1:
            notes.append(f"{sid_}: log có {len(seen_t)} take {seen_t} — dùng '{want}' (field take / --takes để chọn)")
        by_shot[sid_] = [r for r in lst if r.get("take") in (want, None)]
        take_of[sid_] = want
    for r in rows:                                        # viewport/dpr sanity vs footage size
        if r.get("viewport") and r.get("dpr"):
            w = r["viewport"]["w"] * r["dpr"]
            if abs(w - geo.fw) > 2:
                notes.append(f"viewport {r['viewport']['w']}×dpr {r['dpr']} = {w:.0f} px ≠ footage {geo.fw} — sai zoom trình duyệt?")
            break

    def find(shot_id, selector, t_target):
        cand = [r for r in by_shot.get(shot_id, []) if r.get("selector") == selector and r.get("bbox")]
        if not cand:
            return None
        before = [r for r in cand if r["t_epoch"] <= t_target + 0.05]
        return max(before, key=lambda r: r["t_epoch"]) if before else min(cand, key=lambda r: r["t_epoch"])

    warned = set()

    def emit(lst, shot, t_epoch, **kw):
        key = f"{shot['id']}_{take_of[shot['id']]}" if shot["id"] in take_of else shot["id"]
        base = per_shot.get(key, per_shot.get(shot["id"]))
        if base is None:
            base = rec_start
            if per_shot and ("nobase", shot["id"]) not in warned:
                warned.add(("nobase", shot["id"]))
                notes.append(f"{shot['id']}: không có rec_start riêng ('{key}') — dùng rec_start chung (giờ có thể sai)")
        t_src = round(t_epoch - base, 3)   # PATCH v3: giờ trong FILE của shot
        m = tl.map(t_src, shot)
        if m is None:
            notes.append(f"{shot['id']}: mốc t_src={t_src} không nằm trong clip nào (footage.json) — bỏ")
            return
        lst.append({"shot": shot["id"], **m, "t_src": t_src, **kw})

    for sid, shot in shots.items():
        if shot.get("capture") is False:
            continue
        log = sorted(by_shot.get(sid, []), key=lambda r: r["t_epoch"])
        if not log:
            notes.append(f"{sid}: KHÔNG có dòng log nào — shot chưa quay hoặc agent không ghi log")
            continue
        t0 = log[0]["t_epoch"]
        # cursor: every interaction with a bbox; click/type = arrive 0.15 s before + click ripple
        seen = set()
        for r in log:
            if r.get("action") in ("zoom", "zoom_out"):             # PATCH v3: zoom tại nguồn = footage ĐÃ phóng; ghi mốc để dựng biết
                emit(camera, shot, r["t_epoch"], source_zoom=float(r.get("level", 1.0)) if r["action"] == "zoom" else 1.0,
                     box=geo.box(r) if r.get("bbox") else None, note="zoom TẠI NGUỒN — không nhân thêm camera hậu kỳ")
                continue
            if not r.get("bbox") or r.get("action") not in NEEDS_SELECTOR:
                continue
            bx = geo.box(r)
            if not geo.inside(bx):
                notes.append(f"{sid}: bbox '{r.get('selector')}' {bx} nằm ngoài footage {geo.fw}×{geo.fh}")
            x, y = round(bx[0] + bx[2] / 2, 1), round(bx[1] + bx[3] / 2, 1)
            if r["action"] == "click":                      # arrive 0.15 s early, then ripple
                emit(cursor, shot, r["t_epoch"] - 0.15, x=x, y=y, act="move")
                emit(cursor, shot, r["t_epoch"], x=x, y=y, act="click")
            elif r["action"] == "type":                     # typing: be there, no ripple
                if r.get("selector") not in seen:
                    emit(cursor, shot, r["t_epoch"] - 0.15, x=x, y=y, act="move")
            else:
                emit(cursor, shot, r["t_epoch"], x=x, y=y, act="move")
            seen.add(r.get("selector"))
        for sel in shot.get("cursor") or []:
            if sel not in seen:
                r = find(sid, sel, t0 + 1e9)
                if r:
                    bx = geo.box(r)
                    emit(cursor, shot, r["t_epoch"], x=round(bx[0] + bx[2] / 2, 1), y=round(bx[1] + bx[3] / 2, 1), act="move")
                else:
                    notes.append(f"{sid}: cursor đi qua '{sel}' nhưng log không có bbox")
        # camera
        for c in shot.get("camera") or []:
            te = t0 + float(c.get("t_rel", 0))
            r = find(sid, c.get("zoom_to"), te) if isinstance(c.get("zoom_to"), str) else None
            if isinstance(c.get("zoom_to"), dict):             # explicit bbox in footage px {x,y,w,h}
                b = c["zoom_to"]
                bx = [b["x"], b["y"], b["w"], b["h"]]
            elif r:
                bx = geo.box(r)
            else:
                notes.append(f"{sid}: camera zoom_to '{c.get('zoom_to')}' không có bbox trong log")
                continue
            want = float(c.get("level", 1.3))
            fx, fy, s = geo.camera(bx, want)
            extra = {"note": f"level {want} -> {s} (giới hạn {geo.max_zoom}× / vừa khung)"} if s < want else {}
            emit(camera, shot, te, fx=fx, fy=fy, scale=s, ease=c.get("ease", "power3.inOut"), dur=float(c.get("dur", 0.7)),
                 box=bx, **extra)
            if c.get("zoom_out_at") is not None:
                emit(camera, shot, t0 + float(c["zoom_out_at"]), fx=geo.fw / 2, fy=geo.fh / 2, scale=1.0,
                     ease=c.get("ease", "power3.inOut"), dur=float(c.get("dur", 0.7)), box=[0, 0, geo.fw, geo.fh])
        # highlight
        for h in shot.get("highlight") or []:
            te = t0 + float(h.get("t_rel", 0))
            r = find(sid, h.get("selector"), te)
            if not r:
                notes.append(f"{sid}: highlight '{h.get('selector')}' không có bbox trong log")
                continue
            emit(highlight, shot, te, dur=float(h.get("dur", 1.5)), kind=h.get("kind"), text=h.get("text", ""), box=geo.box(r))
        # privacy boxes
        for a in (shot.get("avoid") or []) + (sc.get("global_avoid") or []):
            for r in [q for q in log if q.get("selector") == a.get("selector") and q.get("bbox")]:
                emit(privacy, shot, r["t_epoch"], box=geo.box(r), reason=a.get("reason", ""))

    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    key = lambda e: (e.get("scene", ""), e["t"])  # noqa: E731
    for name, data in (("cursor-path", sorted(cursor, key=key)), ("camera-cues", sorted(camera, key=key)),
                       ("highlight-cues", sorted(highlight, key=key)), ("privacy-boxes", sorted(privacy, key=key))):
        (out / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"cursor": len(cursor), "camera": len(camera), "highlight": len(highlight), "privacy": len(privacy),
            "footage": f"{geo.fw}x{geo.fh}", "notes": notes}


# ------------------------------------------------------------------ cli
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    pd = sub.add_parser("draft", help="feature-map (RECON) -> nháp kịch bản quay theo dạng app")
    pd.add_argument("--feature-map", required=True)
    pd.add_argument("--out", required=True, help=".yaml hoặc .json")
    sub.add_parser("snippet", help="in đoạn JS lấy 1 dòng capture log (dán vào javascript_tool, thay SELECTOR/FALLBACK_TEXT)")
    pl = sub.add_parser("lint", help="cổng G0: kiểm kịch bản quay TRƯỚC khi quay")
    pl.add_argument("--script", required=True)
    pl.add_argument("--web-data", help="mặc định: trường web_data trong kịch bản")
    pb = sub.add_parser("build", help="log bbox lúc quay -> cursor/camera/highlight/privacy JSON")
    pb.add_argument("--script", required=True)
    pb.add_argument("--log", required=True, help="capture log JSON Lines")
    pb.add_argument("--rec-start", type=float, help="epoch lúc ffmpeg bắt đầu ghi")
    pb.add_argument("--markers", help="markers.txt có dòng `rec_start <epoch>`")
    pb.add_argument("--footage", help="data/footage.json của cut_clips.py -> quy ra giờ phim + scene")
    pb.add_argument("--takes", default="", help="chọn take theo shot: R01-boms=t5,R08-kho=t2 (mặc định: field take, hoặc take CUỐI trong log)")
    pb.add_argument("--out", default="data")
    pb.add_argument("--allow-unmeasured", action="store_true",
                    help="chạy build dù capture.crop_top_measured chưa true (CHỈ để thử, toạ độ có thể sai)")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):          # REVIEW 27/09: Windows cp1252 làm lint crash khi in tiếng Việt
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if a.cmd == "snippet":
        print(JS_SNIPPET)
        return 0
    if a.cmd == "draft":
        d = draft(load_script(a.feature_map))
        out = pathlib.Path(a.out)
        if out.suffix.lower() in (".yaml", ".yml"):
            import yaml  # noqa: PLC0415
            txt = "# NHÁP sinh từ feature-map — viết vo_line/anchor_word, chỉnh thời gian, rồi chạy lint (G0)\n" + \
                yaml.safe_dump(d, allow_unicode=True, sort_keys=False, width=140)
        else:
            txt = json.dumps(d, ensure_ascii=False, indent=1)
        out.write_text(txt, encoding="utf-8")
        print(f"draft: {len(d['shots'])} shot -> {out}")
        return 0
    sc = load_script(a.script)
    if a.cmd == "lint":
        err, warn, total = lint(sc, a.web_data)
        for w in warn:
            print("WARN ", w)
        for e in err:
            print("FAIL ", e)
        n = len(sc.get("shots", []))
        print(f"G0 {'PASS' if not err else 'FAIL'}: {n} shot, tổng duration_target {total:.1f} s, {len(err)} lỗi, {len(warn)} cảnh báo")
        return 0 if not err else 1
    cap = sc.get("capture", {})
    if "crop_top" in cap and cap.get("crop_top_measured") is not True and not a.allow_unmeasured:
        print("FAIL build: capture.crop_top_measured != true — đo P9 (crop_top, viewport_css, dpr) trên khung gfxcapture "
              "thật rồi đổi cờ; hoặc --allow-unmeasured để thử")
        return 2
    rows = load_log(a.log)
    takes = dict(x.split("=", 1) for x in a.takes.split(",") if "=" in x)
    res = build(sc, rows, rec_start_from(a, rows), a.footage, a.out, rec_starts_per_shot(a, rows), takes)
    for n in res.pop("notes"):
        print("NOTE ", n)
    print("build:", json.dumps(res, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
