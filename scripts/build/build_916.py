#!/usr/bin/env python3
"""build_916.py - make the 9:16 project folder from the 16:9 composition (a SEPARATE folder = no write race with the 16:9
render, no hyperframes lint `multiple_root_compositions`; LESSON-06/12). Centred split layout: app panel on top, hero slot
under it, captions below - numbers from project.json "nine_sixteen" (defaults = the skill layout: app 1040x547 @ y 365,
hero 1040x440 @ y 952, caption y 1450). qa/check_layout_9x16.py reads the CSS variables written here.

STATUS: SMOKE-TESTED (27/09 ProfitBase build_916_v3.py; generalised = src/dst dirs as args/config, layout numbers from
        config, engine-specific overrides in nine_sixteen.extra_css. Re-run here on a synthetic index.html + check_layout)

  python scripts/build/build_916.py --config project.json [--src comp] [--dst comp-9x16]

Copies lib/ scenes/ data/ assets/ + tokens.css hyperframes.json (those that exist) and index.html with: class p916 on
<html>, 1080x1920 root, viewport meta, the layout CSS block before the first </style>, <div id="heroslot"> before
nine_sixteen.hero_before (default '<div id="titles" class="layer">'). The dst folder is DELETED and rebuilt every run.
"""
import argparse
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.config import read_config, utf8_stdout  # noqa: E402

# Engine-specific overrides of the 27/09 ProfitBase composition (class names of its overlay layers). Kept as the default
# for the repo's engine; replace with nine_sixteen.extra_css when your composition uses other classes.
DEFAULT_EXTRA_CSS = """
      html.p916 .ttl { left: 60px; top: 96px; width: 960px; }
      html.p916 .ttl .t1, html.p916 .ttl .t2 { font-size: 64px !important; }
      html.p916 .callout { left: 40px !important; top: 972px !important; width: 1000px !important; max-height: 400px; box-shadow: none; background: transparent; }
      html.p916 .callout .v { font-size: 56px; } html.p916 .callout .row { font-size: 28px; }
      html.p916 .giant { left: 60px !important; top: 1010px !important; font-size: 132px !important; }
      html.p916 #strip-1, html.p916 .mods, html.p916 #chip, html.p916 .curve { display: none !important; }
      html.p916 #strip-2 { left: 60px; top: 1010px; width: 960px !important; }
      html.p916 .lock { top: 30px !important; left: 56px !important; }
      html.p916 .cap2 { width: 1080px; top: var(--cap-y); white-space: normal; padding: 0 30px; }
      html.p916 .cap2 span { font-size: 80px; }
      html.p916 #draft { top: 1880px; }
"""


def css_block(n):
    ax, ay, aw, ah = n.get("app", [20, 365, 1040, 547])
    hx, hy, hw, hh = n.get("hero", [20, 952, 1040, 440])
    cy, ch, rad = n.get("cap_y", 1450), n.get("cap_h", 105), n.get("radius", 28)
    return f"""
      /* ===== 9:16 centred split (LESSON-12) - qa/check_layout_9x16.py reads these variables ===== */
      :root {{ --W: 1080px; --H: 1920px; --app-x: {ax}px; --app-y: {ay}px; --app-w: {aw}px; --app-h: {ah}px;
              --hero-x: {hx}px; --hero-y: {hy}px; --hero-w: {hw}px; --hero-h: {hh}px; --cap-y: {cy}px; --cap-h: {ch}px; --radius: {rad}px; }}
      html.p916 #root {{ width: 1080px; height: 1920px; }}
      html.p916 .layer {{ width: 1080px; height: 1920px; }}
      html.p916 #heroslot {{ position: absolute; left: var(--hero-x); top: var(--hero-y); width: var(--hero-w); height: var(--hero-h);
              border-radius: var(--radius); background: #fff; box-shadow: 0 30px 80px rgba(30,25,70,.14), 0 0 0 1px rgba(105,82,224,.14); }}
""" + n.get("extra_css", DEFAULT_EXTRA_CSS)


def main():
    utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=None)
    ap.add_argument("--src", default=None, help="16:9 composition dir (default paths.comp_dir)")
    ap.add_argument("--dst", default=None, help="9:16 project dir (default paths.comp_916_dir)")
    a = ap.parse_args()
    cfg = read_config(a.config or "project.json", required=bool(a.config))
    ROOT = pathlib.Path(a.src) if a.src else cfg.comp()
    DST = pathlib.Path(a.dst) if a.dst else cfg.p("comp_916_dir")
    n = cfg.get("nine_sixteen", {})
    if DST.resolve() == ROOT.resolve():
        raise SystemExit("dst == src: the 9:16 project must be a separate folder")
    if DST.exists():
        shutil.rmtree(DST)
    DST.mkdir(parents=True)
    for d in ["lib", "scenes", "data", "assets"]:
        if (ROOT / d).exists():
            shutil.copytree(ROOT / d, DST / d)
    for f in ["tokens.css", "hyperframes.json"]:
        if (ROOT / f).exists():
            shutil.copy2(ROOT / f, DST / f)
    h = (ROOT / "index.html").read_text(encoding="utf-8")
    reps = [(n.get("html_tag", '<html lang="vi" data-resolution="landscape">'), n.get("html_tag_916", '<html lang="vi" class="p916" data-resolution="portrait">')),
            ('data-width="1920" data-height="1080"', 'data-width="1080" data-height="1920"'),
            ('<meta name="viewport" content="width=1920, height=1080">', '<meta name="viewport" content="width=1080, height=1920">'),
            ("    </style>", css_block(n) + "    </style>")]
    anchor = n.get("hero_before", '<div id="titles" class="layer">')
    reps.append((anchor, '<div id="heroslot"></div>' + chr(10) + "      " + anchor))   # behind titles/strip
    for old, new in reps:
        if old not in h:
            raise SystemExit(f"index.html: anchor not found: {old!r} (set nine_sixteen.html_tag / hero_before for your engine)")
        h = h.replace(old, new, 1)
    assert h.count('class="p916"') == 1 and "heroslot" in h
    (DST / "index.html").write_text(h, encoding="utf-8")
    print(f"9x16 project -> {DST}")


if __name__ == "__main__":
    main()
