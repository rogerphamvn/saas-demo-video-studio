"""e0_gate.py - environment gate E0 (SKILL 5.0), run BEFORE the first shot. Windows. Each check = a real failure of 27/09.

STATUS: SMOKE-TESTED (new; checks 1-2 run live on the dev machine, check 3 run with --motion-file on a synthetic clip.
        The live --motion capture path (gfxcapture) was not run here)

  python scripts/capture/e0_gate.py [--config project.json] [--motion 10 | --motion-file footage/gate.mkv]

 1 APPS    no other AI agent app running (tasklist image names containing e0.forbidden_apps, default codex, chatgpt).
           27/09: a second agent attached to the same Chrome -> the debugger bar flipped between agents, ~1 frame/s.
 2 CHROME  a main chrome.exe process (no --type=) has the 4 anti-throttle flags:
             --disable-backgrounding-occluded-windows --disable-renderer-backgrounding
             --disable-background-timer-throttling --disable-features=CalculateNativeWinOcclusion
           and that process is NOT a --no-startup-window background instance ("keep running in background" swallows new
           flags: taskkill Chrome completely, then relaunch with the flags; add --start-fullscreen to skip F11).
 3 MOTION  (optional) record N s of monitor 0 while the page is moving (scroll/translate it during the test!) and measure
           changed frames/s over the moving span (first to last changed frame): >= 25 PASS (normal capture) · 10-25 WARN = HOLD mode (hold >= 2 s after
           every change) · < 10 FAIL (stop, do not burn retakes).
 NOT checked here (do it in the browser tool): the capture tab is the VISIBLE tab (document.visibilityState === 'visible').
Prints PASS/WARN/FAIL lines (command lines are never printed - they can hold profile paths); exit 1 on any FAIL.
"""
import json
import pathlib
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib.config import load_config  # noqa: E402
from motion import segments  # noqa: E402

FLAGS = ["--disable-backgrounding-occluded-windows", "--disable-renderer-backgrounding", "--disable-background-timer-throttling"]
FEATURE = "CalculateNativeWinOcclusion"


def check_apps(forbidden):
    out = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    names = sorted({ln.split('","')[0].strip('"') for ln in out.splitlines() if ln.startswith('"')})
    hits = sorted({n for n in names for f in forbidden if f.lower() in n.lower()})
    return (not hits, f"APPS forbidden {forbidden}: " + (f"RUNNING {hits}" if hits else f"none of {len(names)} images match"))


def chrome_mains():
    ps = ("Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | "
          "Select-Object ProcessId,ParentProcessId,CommandLine | ConvertTo-Json -Compress")
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, encoding="utf-8", errors="replace")
    txt = r.stdout.strip()
    if not txt:
        return []
    data = json.loads(txt)
    data = data if isinstance(data, list) else [data]
    return [d for d in data if d.get("CommandLine") and "--type=" not in d["CommandLine"]]


def flag_report(cmd):
    have = [f for f in FLAGS if f in cmd]
    feats = []
    for tok in cmd.split():
        if tok.strip('"').startswith("--disable-features="):
            feats += tok.strip('"').split("=", 1)[1].split(",")
    missing = [f for f in FLAGS if f not in have] + ([] if FEATURE in feats else [f"--disable-features={FEATURE}"])
    return missing, "--no-startup-window" in cmd


def check_chrome():
    mains = chrome_mains()
    if not mains:
        return False, ["CHROME no chrome.exe main process found - launch Chrome with the 4 flags first"]
    lines, good = [], []
    for d in mains:
        missing, bg = flag_report(d["CommandLine"])
        tag = f"pid {d['ProcessId']}"
        if not missing and not bg:
            good.append(tag)
            lines.append(f"CHROME {tag}: 4/4 anti-throttle flags, not a background instance")
        elif not missing and bg:
            lines.append(f"CHROME {tag}: flags present BUT --no-startup-window (background instance) - taskkill + relaunch")
        else:
            lines.append(f"CHROME {tag}: missing {missing}" + (" + --no-startup-window background instance" if bg else ""))
    return bool(good), lines


def check_motion(cfg, seconds, file, fps):
    if not file:
        tmp = pathlib.Path(tempfile.mkdtemp()) / "e0_motion.mkv"
        mon = int(cfg.get2("capture.monitor_idx", 0))
        vf = (f"gfxcapture=monitor_idx={mon}:capture_cursor=0:max_framerate=60,hwdownload,format=bgra,"
              "crop=trunc(iw/2)*2:trunc(ih/2)*2:0:0,fps=60,format=yuv420p")
        print(f"recording {seconds} s of monitor {mon} - MOVE the page now (scroll / translate) ...", flush=True)
        r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", vf, "-t", str(seconds),
                            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18", "-y", str(tmp)], capture_output=True, text=True)
        if r.returncode:
            return "FAIL", f"MOTION capture failed: {r.stderr.strip()[-300:]}"
        file = tmp
        fps = 60.0
    segs = segments(file, 0, seconds or 3600, fps)
    if not segs:
        return "FAIL", "MOTION no motion segment at all - was the page moving during the test?"
    # rate over the whole moving SPAN (first to last motion frame). Summing per-segment rates is wrong at low frame rates:
    # motion.py bridges gaps of <= 3 frames only, so a 12 changes/s capture splits into 1-frame segments of "60 fps" each.
    span = segs[-1][1] - segs[0][0]
    frames = span * fps
    changed = sum(s[3] for s in segs)
    rate = changed / span if span > 0 else 0.0
    hi, lo = float(cfg.get2("e0.motion_pass_fps", 25)), float(cfg.get2("e0.motion_fail_fps", 10))
    verdict = "PASS" if rate >= hi else "WARN" if rate >= lo else "FAIL"
    mode = {"PASS": "normal capture", "WARN": "HOLD mode (hold >= 2 s after every change)", "FAIL": "STOP - fix the environment"}[verdict]
    return verdict, (f"MOTION {len(segs)} segment(s) over {span:.1f} s, {changed} changed frames -> {rate:.1f} changed/s "
                     f"(pass >= {hi:g}, fail < {lo:g}) -> {mode}")


def main():
    cfg, a = load_config(required=False, description=__doc__, extra=lambda ap: (
        ap.add_argument("--motion", type=float, default=0, help="seconds of live monitor capture for check 3 (0 = skip)"),
        ap.add_argument("--motion-file", default=None, help="measure an existing capture instead of recording"),
        ap.add_argument("--fps", type=float, default=60.0, help="fps of --motion-file"),
        ap.add_argument("--skip-apps", action="store_true"), ap.add_argument("--skip-chrome", action="store_true")))
    fails = 0
    if not a.skip_apps:
        ok, msg = check_apps(cfg.get2("e0.forbidden_apps", ["codex", "chatgpt"]))
        print(("PASS " if ok else "FAIL ") + msg)
        fails += not ok
    if not a.skip_chrome:
        ok, lines = check_chrome()
        for ln in lines:
            print(("PASS " if ok and "4/4" in ln else "FAIL " if not ok else "INFO ") + ln)
        fails += not ok
    if a.motion or a.motion_file:
        v, msg = check_motion(cfg, a.motion, a.motion_file, a.fps)
        print(f"{v} {msg}")
        fails += v == "FAIL"
    print(f"E0 {'PASS' if not fails else 'FAIL'} ({fails} failing check(s))")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
