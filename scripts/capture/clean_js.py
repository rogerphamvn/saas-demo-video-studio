"""clean_js.py - build the paste-ready privacy/clean-up block: js/sdv-clean.template.js + project.json "privacy" inlined.

STATUS: SMOKE-TESTED (new; run here on the example config, output passed `node --check` and the headless test page)

  python scripts/capture/clean_js.py --config project.json [--out footage/sdv-clean.js] [--with-helpers]

--with-helpers appends js/sdv-capture-helpers.js so ONE paste injects both (27/09: re-inject after every reload).
Keys of "privacy" (all optional; unknown keys are reported):
  label              text shown instead of the account name / e-mail (e.g. "ProfitBase Demo")
  hide_visibility    [css selector]  visibility:hidden (floating chat button, toaster)
  hide_selectors     [css selector]  display:none (admin menu items, links to forbidden pages)
  mask_selectors     [css selector | {selector, label}]  children hidden + label drawn (profile block with the e-mail)
  css                [raw css rule]
  hide_groups        [{root, leaf_re, flags, closest}]  hide the `closest` ancestor of a leaf whose text matches
  hide_leaf_text     [regex]  hide leaves (badges "NEW", dev notes)
  replace_text       [{re, flags, with, hide_if_left}]  e.g. strip an AI model name suffix
  replace_emails     true (default) - any e-mail in a leaf -> label
  split_text         [{container, starts_re, after_re, stop_re, with}]  greeting split into several text nodes
  old_names_re       regex of old/real record names that must not be seen; keep_re = demo marker that overrides it
  old_rows           [{root, leaf_re, closest}]  rows whose leaf mentions an old name are hidden
  svg_blank_old      true (default) - chart labels with an old name are blanked
  routes             [{path_prefix, hide_rows:{selector, keep_re}, hide_blocks:{root, leaf_re, container_class_re},
                       listbox:{trigger_text_re, in_dialog, keep_re}}]
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.config import load_config  # noqa: E402

KEYS = {"label", "hide_visibility", "hide_selectors", "mask_selectors", "css", "hide_groups", "hide_leaf_text", "replace_text",
        "replace_emails", "split_text", "old_names_re", "keep_re", "old_rows", "svg_blank_old", "routes", "_doc"}
HERE = pathlib.Path(__file__).resolve().parent


def render(privacy: dict, with_helpers: bool = False) -> str:
    unknown = sorted(set(privacy) - KEYS)
    if unknown:
        print(f"WARN privacy: unknown key(s) {unknown} (known: {sorted(KEYS)})", file=sys.stderr)
    for k in ("old_names_re", "keep_re"):
        if privacy.get(k):
            re.compile(privacy[k])                     # fail here, not silently in the browser
    tpl = (HERE / "js" / "sdv-clean.template.js").read_text(encoding="utf-8")
    js, n = re.subn(r"/\*SDV_CFG\*/.*?/\*END_SDV_CFG\*/", lambda m: json.dumps({k: v for k, v in privacy.items() if k != "_doc"},
                                                                                ensure_ascii=False), tpl, flags=re.S)
    if n != 1:
        raise SystemExit("template marker /*SDV_CFG*/.../*END_SDV_CFG*/ not found exactly once")
    if with_helpers:
        js = js.rstrip() + ";\n" + (HERE / "js" / "sdv-capture-helpers.js").read_text(encoding="utf-8")
    return js


if __name__ == "__main__":
    cfg, a = load_config(extra=lambda ap: (ap.add_argument("--out", default=None, help="default: <footage_dir>/sdv-clean.js"),
                                           ap.add_argument("--with-helpers", action="store_true")), description=__doc__)
    priv = cfg.get("privacy")
    if not priv:
        raise SystemExit('project.json has no "privacy" section - see scripts/project.example.json')
    out = pathlib.Path(a.out) if a.out else cfg.p("footage_dir") / "sdv-clean.js"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(priv, a.with_helpers), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size} bytes) - paste the whole file into javascript_tool after every reload")
