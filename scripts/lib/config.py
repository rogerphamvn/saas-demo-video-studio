"""Shared config loader for every script in scripts/.

STATUS: SMOKE-TESTED (new file; exercised by every smoke run listed in scripts/README.md)

One project = one folder holding `project.json`. Every relative path inside project.json resolves against THAT folder
(not the current directory), so `python scripts/<sub>/<name>.py --config path/to/project.json` works from anywhere.

    from lib.config import load_config
    cfg, args = load_config(extra=lambda ap: ap.add_argument("--only", default=""))
    cfg.p("script_txt")            # Path from cfg["paths"]["script_txt"] (or DEFAULT_PATHS)
    cfg.comp("data/grid.json")     # Path inside the HyperFrames composition folder (paths.comp_dir)
    cfg.get2("grid.bpm", 124)      # dotted lookup with default

API keys: get_key("OPENAI_API_KEY") reads the environment first, then a `.env` file in the CURRENT directory
(tiny KEY=VALUE parser, no quotes/export magic beyond stripping). Keys are never printed.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys

# Default layout of a project folder. Every key can be overridden in project.json -> "paths".
DEFAULT_PATHS = {
    "footage_dir": "footage",                  # raw captures (<shot>_<take>.mkv), markers, capture log
    "markers": "footage/markers.txt",
    "capture_log": "footage/capture-log.jsonl",
    "capture_script": "capture-script.yaml",
    "web_data": "footage/web-data.md",         # numbers measured on the live app (G0 / G3 source of truth)
    "vo_dir": "vo",                            # VO work folder (raw/, raw_var/, lines/, voiceover.wav, captions.json)
    "script_txt": "vo/script.txt",             # one VO line per row: `E1|sentence. sentence.`
    "music_src": "music/source.wav",           # the licensed/generated music file (measured BPM)
    "sfx_plan": "sfx-plan.json",               # SFX plan (see config-examples/sfx-plan.example.json)
    "comp_dir": "comp",                        # HyperFrames composition (index.html, data/, assets/)
    "comp_916_dir": "comp-9x16",               # 9:16 copy (separate folder, LESSON-06/12)
    "deliver_dir": "deliver",
    "qa_dir": "renders/qa",
    "stems_dir": "renders/stems",
}
KNOWN_TOP = {"_doc", "project", "paths", "capture", "e0", "privacy", "vo", "grid", "music", "build", "captions", "mix", "srt",
             "nine_sixteen", "qa", "numbers", "pointer_rule"}


class Cfg(dict):
    """dict + .root (folder of project.json) + path helpers."""

    root: pathlib.Path = pathlib.Path.cwd()

    def _abs(self, v) -> pathlib.Path:
        q = pathlib.Path(str(v))
        return q if q.is_absolute() else (self.root / q).resolve()

    def p(self, key: str, default=None) -> pathlib.Path:
        v = self.get("paths", {}).get(key, default if default is not None else DEFAULT_PATHS.get(key))
        if v is None:
            raise KeyError(f"paths.{key} missing in project.json (and no default)")
        return self._abs(v)

    def comp(self, rel: str = "") -> pathlib.Path:
        return self.p("comp_dir") / rel if rel else self.p("comp_dir")

    def rel(self, v) -> pathlib.Path:
        """Resolve any value (e.g. a file named in a config section) against the project folder."""
        return self._abs(v)

    def get2(self, dotted: str, default=None):
        cur = self
        for k in dotted.split("."):
            if not isinstance(cur, dict) or k not in cur:
                return default
            cur = cur[k]
        return cur

    def need(self, dotted: str):
        v = self.get2(dotted)
        if v is None:
            raise SystemExit(f"project.json: `{dotted}` is required for this script (see scripts/project.example.json)")
        return v


def utf8_stdout() -> None:
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


def read_config(path: str | os.PathLike | None, required: bool = True) -> Cfg:
    """Load project.json. required=False: a missing DEFAULT ./project.json gives an empty Cfg rooted at cwd."""
    p = pathlib.Path(path or "project.json").resolve()
    if not p.exists():
        if required:
            raise SystemExit(f"config not found: {p} (copy scripts/project.example.json -> project.json)")
        c = Cfg()
        c.root = pathlib.Path.cwd()
        return c
    c = Cfg(json.loads(p.read_text(encoding="utf-8")))
    c.root = p.parent
    unknown = sorted(set(c) - KNOWN_TOP)
    if unknown:
        print(f"WARN project.json: unknown top-level key(s) {unknown} - typo? (known: {sorted(KNOWN_TOP)})", file=sys.stderr)
    unknown_p = sorted(set(c.get("paths", {})) - set(DEFAULT_PATHS))
    if unknown_p:
        print(f"WARN project.json: unknown paths key(s) {unknown_p} - typo? (known: {sorted(DEFAULT_PATHS)})", file=sys.stderr)
    return c


def load_config(argv=None, extra=None, required: bool = True, description: str | None = None):
    """Parse --config (+ extra argparse args via callback). Returns (cfg, args)."""
    utf8_stdout()
    ap = argparse.ArgumentParser(description=description, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=None, help="project.json (default ./project.json)")
    if extra:
        extra(ap)
    a = ap.parse_args(argv)
    # an explicit --config must exist; the implicit ./project.json is optional when required=False
    return read_config(a.config or "project.json", required=bool(a.config) or required), a


def load_json(path) -> dict | list:
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def load_js_object(path) -> dict:
    """Read `window.X = {...};` files written by the generators (captions.js, grid.js, cuts.js)."""
    js = pathlib.Path(path).read_text(encoding="utf-8")
    return json.loads(js[js.index("{"): js.rindex("}") + 1])


def norm_line_id(lid: str) -> str:
    """`E1` / `e01` / `E01` -> `E01` (letters + 2-digit number). Anything else is returned stripped, unchanged."""
    m = re.fullmatch(r"\s*([A-Za-z]+)0*(\d+)\s*", lid)
    return f"{m.group(1).upper()}{int(m.group(2)):02d}" if m else lid.strip()


def read_script_txt(path) -> dict:
    """`E1|text` rows -> {"E01": "text"} (insertion order kept)."""
    out = {}
    for ln in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        if ln.strip() and "|" in ln:
            lid, t = ln.split("|", 1)
            out[norm_line_id(lid)] = t.strip()
    return out


# ---------------------------------------------------------------- secrets
def load_dotenv(path: str | os.PathLike = ".env") -> int:
    """Tiny .env reader: KEY=VALUE per line, '#' comments, optional surrounding quotes. Never overrides the environment."""
    p = pathlib.Path(path)
    if not p.exists():
        return 0
    n = 0
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip().removeprefix("export ").strip()
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        if k and k not in os.environ:
            os.environ[k] = v
            n += 1
    return n


def get_key(*names: str) -> str:
    """First non-empty env var among names (after loading ./.env). Raises RuntimeError naming the vars, never the value."""
    load_dotenv()
    for n in names:
        if os.environ.get(n):
            return os.environ[n]
    raise RuntimeError(f"missing {' / '.join(names)}: set it in the environment or in ./.env")
