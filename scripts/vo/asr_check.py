#!/usr/bin/env python3
"""Pronunciation QC: transcribe WAV files with TWO ASR models (whisper-1 and gpt-4o-transcribe, language vi) and print both
next to each other. Read-only - never changes audio. Two independent ears catch what one misses (27/09: "lãi" heard as
"lại", "Profitbase" as "Profit bass"; a respelled input fixed it - see gen_var.py / takes.json).

STATUS: TESTED (27/09 ProfitBase QC of all 13 lines + variants; generalised = key from env / ./.env instead of the hub
        credential loader. NOT re-run here: it calls a paid API)

  python scripts/vo/asr_check.py vo/lines/E08.wav vo/raw_var/E08.0-retry.wav ...

Key: env OPENAI_API_KEY (or ./.env). Costs a few cents per minute of audio (OpenAI pricing).
"""
import pathlib
import sys

import requests

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.config import get_key, utf8_stdout  # noqa: E402

utf8_stdout()
key = get_key("OPENAI_API_KEY")
for f in sys.argv[1:]:
    res = []
    for m in ("whisper-1", "gpt-4o-transcribe"):
        r = None
        for _try in range(3):
            try:
                with open(f, "rb") as fh:
                    r = requests.post("https://api.openai.com/v1/audio/transcriptions", headers={"Authorization": "Bearer " + key},
                                      files={"file": ("a.wav", fh, "audio/wav")},
                                      data={"model": m, "language": "vi", "response_format": "json"}, timeout=60)
                break
            except requests.exceptions.RequestException as e:
                print("  retry", m, type(e).__name__)
        if r is None:
            res.append("TIMEOUT")
            continue
        res.append(r.json().get("text") if r.status_code == 200 else f"HTTP{r.status_code}")
    print(pathlib.Path(f).name, "| W:", res[0], "| 4o:", res[1])
