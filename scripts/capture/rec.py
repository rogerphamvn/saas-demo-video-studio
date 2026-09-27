"""rec.py - record the screen for ONE shot/take into <out-dir>/<name>.mkv (ffmpeg gfxcapture, Windows 10 2004+ / 11).

STATUS: TESTED (ran every shot of the 27/09 ProfitBase capture; generalisation = output dir / markers / limits as args only.
        The --test-src switch is new and was smoke-run here, see scripts/README.md)

  python scripts/capture/rec.py R01-boms_t1 [--config project.json] [--out-dir footage] [--markers footage/markers.txt] [-t 900]

- Source: gfxcapture monitor_idx=0 (DEFAULT). Capturing by window (set env SDV_HWND=<hwnd> or --hwnd) FROZE on 27/09 when the
  "debugging this browser" bar appeared/disappeared (window surface changes) -> keep the monitor default unless you know why.
- Writes `rec_start <epoch of first frame> <name>` to the markers file as soon as ffmpeg reports the first output time,
  and `rec_stop <epoch> <name>` at the end. Browser Date.now()/1000 and Python time.time() read the same OS clock.
- Stops when the file STOP_<name> appears in the out dir (sends 'q' to ffmpeg), or after -t seconds (default 900:
  -t 150 cut a 2.5 min shot short on 27/09). READY_<name> holds the rec_start epoch while recording.
- Frame: cropped to even size (a 1920x1079 first frame made x264 refuse), padded to --w x --h, 60 fps, CRF 14, GOP 60, bt709.
- --test-src 'testsrc2=size=1920x1080:rate=60' replaces gfxcapture with a lavfi test pattern (pipeline test, no screen).
"""
import argparse
import os
import pathlib
import subprocess
import sys
import threading
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.config import read_config, utf8_stdout  # noqa: E402

utf8_stdout()
ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("name", help="output base name, e.g. R01-boms_t1")
ap.add_argument("maxsec", nargs="?", default=None, help="(legacy positional) same as -t")
ap.add_argument("--config", default=None)
ap.add_argument("--out-dir", default=None, help="default: paths.footage_dir")
ap.add_argument("--markers", default=None, help="default: paths.markers")
ap.add_argument("-t", dest="t", default=None, help="max seconds (default capture.max_seconds or 900)")
ap.add_argument("--monitor", type=int, default=None, help="gfxcapture monitor_idx (default capture.monitor_idx or 0)")
ap.add_argument("--hwnd", default=os.environ.get("SDV_HWND", ""), help="capture one window instead (env SDV_HWND)")
ap.add_argument("--w", type=int, default=None)
ap.add_argument("--h", type=int, default=None)
ap.add_argument("--test-src", default=None, help="lavfi source instead of gfxcapture (testing only)")
a = ap.parse_args()
cfg = read_config(a.config or "project.json", required=bool(a.config))
C = cfg.get("capture", {})
D = pathlib.Path(a.out_dir) if a.out_dir else cfg.p("footage_dir")
D.mkdir(parents=True, exist_ok=True)
MARK = pathlib.Path(a.markers) if a.markers else cfg.p("markers")
MARK.parent.mkdir(parents=True, exist_ok=True)
name = a.name
mx = str(a.t or a.maxsec or C.get("max_seconds", 900))
W, H = a.w or C.get("frame", [1920, 1080])[0], a.h or C.get("frame", [1920, 1080])[1]
mon = a.monitor if a.monitor is not None else int(C.get("monitor_idx", 0))
out = D / (name + ".mkv")
stop = D / ("STOP_" + name)
ready = D / ("READY_" + name)
for p in (stop, ready):
    if p.exists():
        p.unlink()
if a.test_src:
    head = a.test_src + ",format=bgra"
else:
    SRC = f"hwnd={a.hwnd}" if a.hwnd else f"monitor_idx={mon}"
    head = f"gfxcapture={SRC}:capture_cursor=0:max_framerate=60,hwdownload,format=bgra"
vf = (f"{head},crop=trunc(iw/2)*2:trunc(ih/2)*2:0:0,pad={W}:{H}:0:0,fps=60,"
      "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p")
cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-stats_period", "0.1", "-progress", "pipe:1", "-f", "lavfi", "-i", vf, "-t", mx,
       "-c:v", "libx264", "-preset", str(C.get("preset", "superfast")), "-crf", str(C.get("crf", 14)), "-g", "60", "-keyint_min", "60",
       "-sc_threshold", "0", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv", "-y", str(out)]
t_launch = time.time()
p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
marked = False
drop = dup = None


def watch():
    while p.poll() is None:
        if stop.exists():
            try:
                p.stdin.write("q")
                p.stdin.flush()
            except Exception:
                pass
            return
        time.sleep(0.05)


threading.Thread(target=watch, daemon=True).start()
for ln in p.stdout:
    ln = ln.strip()
    if ln.startswith("out_time_us=") and not marked:
        us = int(ln.split("=")[1]) if ln.split("=")[1].lstrip("-").isdigit() else 0
        if us > 0:
            t0 = time.time() - us / 1e6
            with open(MARK, "a", encoding="utf-8") as m:
                m.write(f"rec_start {t0:.3f} {name}\n")
            ready.write_text(f"{t0:.3f}")
            marked = True
    elif ln.startswith("dup_frames="):
        dup = ln.split("=")[1]
    elif ln.startswith("drop_frames="):
        drop = ln.split("=")[1]
    elif ln and ln.split("=")[0] not in ("frame", "fps", "stream_0_0_q", "bitrate", "total_size", "out_time_ms", "out_time",
                                         "speed", "progress", "out_time_us"):
        print(ln)
p.wait()
t1 = time.time()
with open(MARK, "a", encoding="utf-8") as m:
    m.write(f"rec_stop {t1:.3f} {name}\n")
print(f"DONE {name} exit={p.returncode} launch={t_launch:.3f} stop={t1:.3f} dup={dup} drop={drop} -> {out}")
