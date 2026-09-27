"""Headless test of the browser JS: clean_js.py(render) + js/sdv-clean.template.js + js/sdv-capture-helpers.js on a SYNTHETIC
page (no real app, no network). Needs `pip install playwright` + `python -m playwright install chromium`; prints SKIP otherwise.
Run: python scripts/capture/tests/test_clean_js.py"""
import json
import pathlib
import sys
import tempfile

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import clean_js  # noqa: E402

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("SKIP playwright not installed")
    sys.exit(0)

ACCOUNT = "someaccount"
MAIL = ACCOUNT + "." + "demo" + "@" + "example" + ".com"      # built at run time: no literal address in the repo
PAGE = f"""<!doctype html><html><head><meta charset="utf-8"></head><body>
<aside><a href="/profile"><span class="em">{MAIL}</span><span>Super Admin</span></a>
 <a href="/admin/users">Users admin</a>
 <ul><li><button><span>ADMIN DASHBOARD</span></button><ul><li>Logs</li></ul></li><li><span>Reports</span></li></ul></aside>
<main>
 <h1 id="greet"></h1>
 <p id="mailp">Signed in as {MAIL}</p>
 <span id="badge">NEW</span> <span id="model">Finance expert • Model X 4.8</span>
 <div class="group" id="tip1"><a><p>Batch "Old Alpha" needs stock</p></a></div>
 <div class="group" id="tip2"><a><p>Batch "Demo · Candle" looks healthy</p></a></div>
 <svg width="200" height="40"><text id="svgold" x="5" y="15">Old Alpha</text><text id="svgdemo" x="5" y="35">Demo · Candle</text></svg>
 <table><tbody><tr id="r1"><td>Demo · Wax</td></tr><tr id="r2"><td>Old Beta</td></tr></tbody></table>
 <div role="dialog"><button role="combobox" aria-expanded="true" aria-controls="lb1">Choose material</button>
  <div role="listbox" id="lb1"><div role="option" id="o1">Demo · Wax</div><div role="option" id="o2">Old Beta</div></div></div>
 <div><span>Ads fee</span><input id="f1"></div> <div><span>Tax</span><div><input id="f2"></div></div>
 <button id="target" style="margin:40px">Save plan</button>
</main>
<script>document.getElementById('greet').append('Good evening', ', ', '{ACCOUNT}', '! ');</script>
</body></html>"""
PRIV = {"label": "Demo Label", "hide_selectors": ['aside a[href^="/admin"]'], "mask_selectors": ['aside a[href="/profile"]'],
        "hide_groups": [{"root": "aside", "leaf_re": "^\\s*admin dashboard\\s*$", "flags": "i", "closest": "li"}],
        "hide_leaf_text": ["^\\s*NEW\\s*$"], "replace_text": [{"re": "\\s*[•·]\\s*Model X[\\s\\d.]*", "with": ""}],
        "split_text": [{"container": "h1", "starts_re": "^\\s*Good evening"}],
        "old_names_re": "Old Alpha|Old Beta", "keep_re": "Demo ·",
        "old_rows": [{"root": "main", "leaf_re": "^\\s*Batch \"", "closest": "div.group"}],
        "routes": [{"hide_rows": {"selector": "main tbody tr", "keep_re": "^\\s*Demo ·"},
                    "listbox": {"trigger_text_re": "Choose material", "in_dialog": True, "keep_re": "^\\s*Demo ·"}},
                   {"path_prefix": "/never-here", "hide_rows": {"selector": "main tbody tr", "keep_re": "^$"}}]}

res = []


def check(name, cond):
    res.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name)


js = clean_js.render(PRIV, with_helpers=True)
with tempfile.TemporaryDirectory() as td:
    page_path = pathlib.Path(td) / "app.html"
    page_path.write_text(PAGE, encoding="utf-8")
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1280, "height": 800})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(page_path.as_uri())
        ret = pg.evaluate(js)
        check("block returns the helpers banner (both IIFEs ran)", ret == "sdv-capture-helpers on")
        txt = pg.inner_text("body")
        check("no e-mail and no account name in visible text", MAIL not in txt and ACCOUNT not in txt)
        check("greeting split node replaced by label", "Demo Label" in pg.inner_text("#greet"))
        check("mail in paragraph replaced", pg.inner_text("#mailp") == "Signed in as Demo Label")
        check("admin link + admin group hidden, other group kept", "Users admin" not in txt and "ADMIN DASHBOARD" not in txt and "Reports" in txt)
        check("NEW badge hidden, model suffix stripped", "NEW" not in txt.split() and pg.inner_text("#model") == "Finance expert")
        check("old tip row hidden, demo tip row kept", not pg.is_visible("#tip1") and pg.is_visible("#tip2"))
        check("svg old label blanked, demo label kept", pg.get_attribute("#svgold", "data-sdv-blank") == "1"
              and pg.get_attribute("#svgdemo", "data-sdv-blank") is None)
        check("route rule: non-demo table row hidden", pg.is_visible("#r1") and not pg.is_visible("#r2"))
        check("route rule with other path_prefix NOT applied", pg.is_visible("#r1"))
        check("listbox: old option hidden, demo option kept", pg.is_visible("#o1") and not pg.is_visible("#o2"))
        pg.evaluate(f"document.querySelector('main').insertAdjacentHTML('beforeend', '<p id=\"late\">late {MAIL}</p>')")
        pg.wait_for_timeout(400)
        check("observer re-applies to content added later", pg.inner_text("#late") == "late Demo Label")
        line = json.loads(pg.evaluate("__sdvLog('s1', 3, 'click', 'text=Save plan')"))
        check("__sdvLog returns bbox + t_epoch + selector_used", line["bbox"]["w"] > 10 and line["t_epoch"] > 1e9
              and line["selector_used"] == "text=Save plan")
        miss = json.loads(pg.evaluate("__sdvLog('s1', 4, 'click', '#nope', 'Save plan')"))
        check("__sdvLog falls back to fallback_text", miss["selector_used"] == "text=Save plan" and "error" not in miss)
        fill = json.loads(pg.evaluate("__sdvFillByLabels({'Ads fee': '10', 'Tax': 8, 'Missing label': 1})"))
        check("__sdvFillByLabels sets found fields, reports ok:false for a missing label",
              fill == {"ok": False, "set": 2, "of": 3} and pg.input_value("#f1") == "10" and pg.input_value("#f2") == "8")
        z = json.loads(pg.evaluate("__sdvZoom('s1', 5, 'text=Save plan', 1.5, 10)"))
        pg.wait_for_timeout(100)
        check("__sdvZoom transforms body + logs level", "scale(1.5)" in pg.evaluate("document.body.style.transform") and z["level"] == 1.5)
        pg.evaluate("__sdvZoomOut('s1', 6, 10)")
        pg.evaluate("window.__sdvClean.off()")
        check("off() removes the style and the markers", pg.evaluate("!document.getElementById('sdv-clean') && !document.querySelector('[data-sdv-hide]')"))
        check("no page errors", not errs)
        b.close()
n = sum(1 for _, o in res if o)
print(f"PASS {n}/{len(res)}" if n == len(res) else f"FAIL {n}/{len(res)}")
sys.exit(0 if n == len(res) else 1)
