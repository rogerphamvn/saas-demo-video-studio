"""Write capture markers while recording (epoch seconds, one line each) - the only reliable clock between the browser
agent and ffmpeg. Source time of a marker in the raw capture = marker epoch - rec_start epoch.

STATUS: SMOKE-TESTED (hub capture_marker.py copied unchanged apart from this docstring; its use in a real case is not
        recorded, so it was re-run here - see scripts/README.md).
rec.py already writes rec_start/rec_stop per file; use this for extra scene marks or a manual action log.

  python scripts/capture/marker.py footage/markers.txt rec_start      # right when ffmpeg starts
  python scripts/capture/marker.py footage/markers.txt T1_start
  python scripts/capture/marker.py footage/markers.txt act --x 385 --y 300 --what "triple-click Gia ban"   # ACTION LOG line

Action lines (x, y in the SCREENSHOT frame of the browser tool) feed the click/hover list; convert to capture px with the
measured factor (ProfitBase: screenshot 1512x795 -> CSS 1536x808 -> x1.25 dpr -> ~x1.27) and CHECK 1-2 points on a real
frame before trusting it. Never use the log as the cursor path: build it from track_pointer.py (dense 30 fps).
"""
import argparse
import time

ap = argparse.ArgumentParser()
ap.add_argument("file")
ap.add_argument("label")
ap.add_argument("--x", type=float)
ap.add_argument("--y", type=float)
ap.add_argument("--what", default="")
a = ap.parse_args()
t = f"{time.time():.6f}"
line = f"{a.label} {t}" + (f" x={a.x:g} y={a.y:g} {a.what}" if a.x is not None else (f" {a.what}" if a.what else ""))
with open(a.file, "a", encoding="utf-8") as f:
    f.write(line + "\n")
print(line)
