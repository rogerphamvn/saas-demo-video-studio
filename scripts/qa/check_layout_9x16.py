"""9:16 layout gate (qa-gates G11): read the layout CSS variables of a 9:16 composition and check the split layout is

STATUS: TESTED (hub; skeleton 6/6 PASS and the rejected layout FAIL on 26/09; copied unchanged apart from this docstring)
vertically centred and aligned. User 26/09: split layout crowded to the top (app y 200-747, hero 800-1300, caption 1450,
~400 px empty at the bottom) = "bố cục không cân đối giữa màn hình".

Checks (all in px of the 1080x1920 frame):
  |top gap - bottom gap| <= 80    top gap = --app-y ; bottom gap = --H - (--cap-y + --cap-h)
  app and hero share x and width (one aligned column); app height = width * capture_h / capture_w (+-2) -> camera 1.0x shows the whole panel
  order: app bottom <= hero top ; hero bottom <= caption top ; caption bottom <= 1670 (platform UI safe zone)

  python scripts/qa/check_layout_9x16.py comp-9x16/index.html [--capture 1920x1010]
Reads ONLY the declared variables: an element that ignores them (hard-coded top) is not seen -> also look at the 1 fps sheet.
"""
import re
import sys

args = [a for a in sys.argv[1:] if not a.startswith("--")]
cw, ch = map(int, (sys.argv[sys.argv.index("--capture") + 1] if "--capture" in sys.argv else "1920x1010").split("x"))
css = open(args[0], encoding="utf-8").read()
need = ["H", "app-x", "app-y", "app-w", "app-h", "hero-x", "hero-y", "hero-w", "hero-h", "cap-y", "cap-h"]
v = {}
for k in need:
    m = re.search(r"--" + re.escape(k) + r":\s*(-?[\d.]+)px", css)
    if not m:
        sys.exit(f"FAIL missing CSS variable --{k}")
    v[k] = float(m.group(1))
top = v["app-y"]
bottom = v["H"] - (v["cap-y"] + v["cap-h"])
checks = [
    (f"balance: top gap {top:.0f} vs bottom gap {bottom:.0f} (|diff| {abs(top - bottom):.0f} <= 80)", abs(top - bottom) <= 80),
    (f"aligned column: app x/w {v['app-x']:.0f}/{v['app-w']:.0f} = hero x/w {v['hero-x']:.0f}/{v['hero-w']:.0f}",
     v["app-x"] == v["hero-x"] and v["app-w"] == v["hero-w"]),
    (f"app keeps the whole capture at 1.0x: h {v['app-h']:.0f} vs w*{ch}/{cw} = {v['app-w'] * ch / cw:.0f}", abs(v["app-h"] - v["app-w"] * ch / cw) <= 2),
    (f"order: app bottom {v['app-y'] + v['app-h']:.0f} <= hero top {v['hero-y']:.0f}", v["app-y"] + v["app-h"] <= v["hero-y"]),
    (f"order: hero bottom {v['hero-y'] + v['hero-h']:.0f} <= caption top {v['cap-y']:.0f}", v["hero-y"] + v["hero-h"] <= v["cap-y"]),
    (f"caption bottom {v['cap-y'] + v['cap-h']:.0f} <= 1670 safe zone", v["cap-y"] + v["cap-h"] <= 1670),
]
for msg, ok in checks:
    print(("PASS " if ok else "FAIL ") + msg)
sys.exit(0 if all(ok for _, ok in checks) else 1)
