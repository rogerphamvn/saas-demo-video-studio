# scripts/ — the runnable pipeline

Grid-first pipeline for SaaS / web-app review videos from **real screen capture**, as run on the ProfitBase case (27/09/2026):
capture (ffmpeg gfxcapture + a browser agent in macro mode) → Vietnamese VO (VieNeu-TTS, local) → music conformed to a bar grid →
HyperFrames composition (engine/) → ducked mix → QA + 9:16.

- **Python 3.11+** with `numpy`, `scipy`, `Pillow` (+ `requests` for ASR, `pyyaml` for .yaml capture scripts, `playwright` only for the JS test).
- **ffmpeg / ffprobe** on PATH (ffmpeg ≥ 7.1 with `gfxcapture` for recording on Windows 10 2004+/11). Node for `node --check` / the renderer.
- **One config**: every script takes `--config project.json`; every relative path in it resolves against the folder holding
  project.json. Copy `project.example.json` (ProfitBase values, no personal data) and edit. Unknown keys print a WARN.
- **Secrets**: only from environment variables or a `.env` file in the current directory (`OPENAI_API_KEY` for whisper / ASR QC,
  `GEMINI_API_KEY` for the optional Gemini TTS). Never printed. **VieNeu**: env `VIENEU_PY` = python.exe of the VieNeu venv
  (or `--vieneu-python`).
- PowerShell files are 100 % ASCII. Scripts that fail a gate exit 1.

## STATUS legend (first lines of every file)

| STATUS | meaning |
|---|---|
| **TESTED** | ran in the real ProfitBase case; generalisation only touched paths / args / config loading |
| **SMOKE-TESTED** | generalised (or fixed) and re-run in this session on synthetic data — evidence below |
| **UNTESTED** | generalised, not re-run |

Count: **19 TESTED · 21 SMOKE-TESTED · 1 UNTESTED** (41 .py/.js/.ps1 files with a STATUS line; the 5 tests + `lib/__init__.py` have none).

## Project folder (defaults of `paths.*`)

```
my-video/
  project.json             sfx-plan.json            capture-script.yaml
  footage/   <shot>_<take>.mkv  markers.txt  capture-log.jsonl  web-data.md  sdv-clean.js
  vo/        script.txt (E1|sentence…)  adjust.json  takes.json  tts_respell.json  raw/ raw_var/ lines/ voiceover.wav captions.json
  music/     source.wav
  comp/      index.html (engine)  data/{grid,cuts,captions}.js(on)  assets/{footage,audio}/
  comp-9x16/ (generated)   deliver/   renders/{qa,stems}/
```

## Scripts

Stages: 01 brief · 02 recon · 03 storyboard · 04 capture-script+G0 · 05 E0+macro capture · 06 VO · 07 music grid · 08 build · 09 mix · 10 QA+9:16+deliver.

| path | purpose | stage | command | inputs → outputs | STATUS |
|---|---|---|---|---|---|
| lib/config.py | config loader, `.env` reader, line-id normaliser | all | (imported) | project.json → Cfg | SMOKE-TESTED |
| lib/sdv_common.py | audio/video/pointer/HTML-marker helpers | all | (imported) | — | TESTED |
| capture/capture_log_to_edit.py | draft capture script from feature map; **G0 lint**; JS snippet; **build** cursor/camera/highlight/privacy cues from the capture log | 04, 08 | `python scripts/capture/capture_log_to_edit.py lint --script capture-script.yaml --web-data footage/web-data.md` · `… draft --feature-map feature-map.yaml --out capture-script.draft.yaml` · `… snippet` · `… build --script capture-script.yaml --log footage/capture-log.jsonl --markers footage/markers.txt [--takes R01=t5] [--footage comp/data/footage.json] --out comp/data` | script + web-data → G0 PASS/FAIL; log + markers → cursor-path / camera-cues / highlight-cues / privacy-boxes .json | SMOKE-TESTED |
| capture/clean_js.py | build the paste-ready privacy block from `privacy` | 05 | `python scripts/capture/clean_js.py --config project.json [--out footage/sdv-clean.js] [--with-helpers]` | privacy config → sdv-clean.js | SMOKE-TESTED |
| capture/js/sdv-clean.template.js | config-driven privacy/clean-up (CSS hide/mask, text replace, split-node greeting, old-name rows, SVG labels, route rules, listbox options) | 05 | via clean_js.py | — | SMOKE-TESTED |
| capture/js/sdv-capture-helpers.js | `__sdvLog / __sdvZoom / __sdvZoomOut / __sdvScroll / __sdvSet / __sdvField / __sdvFillByLabels` | 05 | paste after the clean block (or `--with-helpers`) | → capture-log lines | SMOKE-TESTED |
| capture/e0_gate.py | **E0 gate**: no other AI agent apps, Chrome anti-throttle flags, optional motion test | 05 | `python scripts/capture/e0_gate.py [--config project.json] [--motion 10 \| --motion-file footage/gate.mkv]` | tasklist, Win32_Process → PASS/WARN/FAIL | SMOKE-TESTED |
| capture/rec.py | record one shot/take (gfxcapture monitor 0, 60 fps, CRF 14), writes rec_start/rec_stop markers, stops on `STOP_<name>` | 05 | `python scripts/capture/rec.py R01-boms_t1 [--config project.json] [--out-dir footage] [--markers footage/markers.txt] [-t 900] [--hwnd N]` | screen → footage/<name>.mkv + markers | TESTED |
| capture/vcheck.py | per-take check: size, unique fps, keyframes, debugger bar, 1 fps sheet | 05 | `python scripts/capture/vcheck.py footage/R01-boms_t1.mkv --sheet [--crop-top 70]` | mkv → JSON line + check/<stem>_sheet.jpg | TESTED |
| capture/motion.py | motion segments + changed frames/s | 05 | `python scripts/capture/motion.py footage/T.mkv 0 10 [--fps 60]` | mkv → segment lines | TESTED |
| capture/flash.py | find a 2×2 px sync flash (bottom-right) | 05 | `python scripts/capture/flash.py footage/R01-boms_t1.mkv 0 30 [--w 1920 --h 1080]` | mkv → times | TESTED |
| capture/ingest.py | packed macro log `step\|action\|t\|bbox\|value\|selector` → capture-log.jsonl | 05 | `python scripts/capture/ingest.py R05-promo t1 --log footage/capture-log.jsonl < packed.txt` | stdin → jsonl | SMOKE-TESTED |
| capture/marker.py | append an epoch marker / manual action line | 05 | `python scripts/capture/marker.py footage/markers.txt T1_start` | → markers.txt | SMOKE-TESTED |
| capture/fg.ps1 | print foreground window hwnd/title/rect | 05 | `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/capture/fg.ps1` | — | TESTED |
| capture/win.ps1 | list/front windows by title → hwnd | 05 | `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/capture/win.ps1 -match 'Google Chrome' [-front]` | — | TESTED |
| capture/keepawake.ps1 | keep the display on during capture | 05 | `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/capture/keepawake.ps1 [-Minutes 150] [-StopFile footage\STOP_KEEPAWAKE]` | — | SMOKE-TESTED |
| capture/tests/*.py | tests of capture_log_to_edit (+ JS) | 04–05 | `python scripts/capture/tests/test_capture_log_to_edit.py` (and test_v3_patch, test_review_fixes, test_log_shape, test_clean_js) | — | see results |
| vo/tts_vn.py | simple one-file VO (Gemini or VieNeu) + captions; library for the grid-first VO scripts | 06 | `python scripts/vo/tts_vn.py vo/script.txt --out vo/simple --engine vieneu --align whisper --align-strict` (`--fake-tts` = offline test) | script → voiceover.wav + captions.json | TESTED |
| vo/vieneu_worker.py | VieNeu inference worker (runs inside the VieNeu venv) | 06 | called by tts_vn / gen_tts / gen_var | sentences.json → NNN.wav | TESTED |
| vo/gen_tts.py | one WAV per sentence (VieNeu), respelling only in TTS input | 06 | `python scripts/vo/gen_tts.py --config project.json [--only E05,E08] [--fake-tts]` | script.txt → vo/raw/wav + manifest.json | SMOKE-TESTED |
| vo/measure.py | onset/offset/inner gap per sentence | 06 | `python scripts/vo/measure.py --config project.json` | manifest → manifest (on/off) | TESTED |
| vo/asr_check.py | 2-ASR pronunciation QC (whisper-1 + gpt-4o-transcribe) — **paid** | 06 | `python scripts/vo/asr_check.py vo/lines/E08.wav vo/raw_var/E08.0-retry.wav` | wav → transcripts | TESTED |
| vo/gen_var.py | pronunciation variants of chosen sentences | 06 | `python scripts/vo/gen_var.py --config project.json vo/variants1.json` | variants → vo/raw_var/*.wav + variants_log.json | TESTED |
| vo/select_takes.py | apply chosen variant takes (vo.takes_file) | 06 | `python scripts/vo/select_takes.py --config project.json` | takes.json → manifest | SMOKE-TESTED |
| vo/assemble.py | join sentences per line, fit to chapter bars, place on grid | 06 | `python scripts/vo/assemble.py --config project.json` | manifest + adjust.json → lines/*.wav, voiceover.wav, placements.json, fit.json | TESTED |
| vo/align.py | word timing per line (whisper-1, cached) + 2–4-word caption groups + text diff gate | 06 | `python scripts/vo/align.py --config project.json [--asr whisper\|none] [--offline]` | lines + placements → captions.json, caption-groups.txt | SMOKE-TESTED |
| music/fit_beat_grid.py | measure BPM / beat0 / per-bar kick+energy of the source | 07 | `python scripts/music/fit_beat_grid.py music/source.wav [--min-bpm 100 --max-bpm 130]` | music → bar table | TESTED |
| music/conform_music.py | splice whole source bars onto the grid (no stretch), delay VO by t0, write grid | 07 | `python scripts/music/conform_music.py --config project.json` | source + voiceover → comp/assets/audio/music-grid*.wav, vo.wav, comp/data/grid.json + grid.js | SMOKE-TESTED |
| music/check_grid.py | downbeat KPI (≤ 40 ms) on the conformed music | 07 | `python scripts/music/check_grid.py --config project.json > renders/qa/grid-check.txt` | music-grid + grid.json → table | SMOKE-TESTED |
| build/cut_clips.py | cut takes into slot clips (crop bar, speed, hold) + cuts.js + `<video>` tags | 08 | `python scripts/build/cut_clips.py --config project.json [--only e04,e05] [--jobs 3]` | comp/data/cuts.json + footage → comp/assets/footage/*.mp4, cuts.js, index.html | SMOKE-TESTED |
| build/erase_pointer.py | remove the extension's orange pointer dot from clips (in place) | 08 | `python scripts/build/erase_pointer.py --config project.json e01 e02 [--probe]` | clips → clips | SMOKE-TESTED |
| build/make_captions_js.py | captions.json → captions.js (t0 shift, no single-word group) | 08 | `python scripts/build/make_captions_js.py --config project.json` | vo/captions.json + grid → comp/data/captions.js | SMOKE-TESTED |
| build/build_916.py | separate 9:16 project, centred split layout | 10 | `python scripts/build/build_916.py --config project.json [--src comp --dst comp-9x16]` | comp → comp-9x16 | SMOKE-TESTED |
| build/track_pointer.py | (fallback, v2) dense pointer track when a take has no capture log | 08 | `python scripts/build/track_pointer.py --config project.json --from 31.2 --to 37.4` | capture.source_capture → comp/data/pointer-track-*.json | UNTESTED |
| audio/build_mix.py | SFX plan → ducked mix → master −14 LUFS / TP ≤ −1 + KPI | 09 | `python scripts/audio/build_mix.py --config project.json` | grid, captions.js, cuts.json, sfx-plan.json, vo/music → comp/assets/audio/mix.wav/.m4a, mix-report.txt, data/sfx-resolved.json, stems | SMOKE-TESTED |
| audio/make_srt.py | .srt identical to the burned-in groups, min cue 0.6 s, text diff 0 | 10 | `python scripts/audio/make_srt.py --config project.json [--out deliver/Name.srt]` | captions.js/json + script → deliver/<project>.srt | SMOKE-TESTED |
| qa/check_sfx.py | independent SFX margin over music (min stereo/mono) | 09 | `python scripts/qa/check_sfx.py --config project.json [--target 6]` | stems + sfx-resolved → renders/qa/sfx-margins.tsv | SMOKE-TESTED |
| qa/check_numbers.py | every overlay number traces to web-data (G3) | 10 | `python scripts/qa/check_numbers.py --config project.json` | comp/index.html + web-data → renders/qa/numbers-vs-webdata.txt | TESTED |
| qa/check_loudness.py | delivered file: −14 ±0.5 LUFS, peak ≤ −1, A/V length, size, fps | 10 | `python scripts/qa/check_loudness.py deliver/final.mp4 --w 1920 --h 1080 --fps 30` | mp4 → PASS/FAIL | TESTED |
| qa/check_shots.py | shot count floor / shot lengths | 10 | `python scripts/qa/check_shots.py renders/draft.mp4 0.3 --out renders/qa` | mp4 → shots-*.txt | TESTED |
| qa/contact_sheet.py | 1 fps time-stamped sheets | 10 | `python scripts/qa/contact_sheet.py renders/draft.mp4 --step 1 --out renders/qa` | mp4 → sheet-*.jpg | TESTED |
| qa/check_layout_9x16.py | 9:16 split layout balanced / aligned (G11) | 10 | `python scripts/qa/check_layout_9x16.py comp-9x16/index.html [--capture 1920x1010]` | index.html → PASS/FAIL | TESTED |

`config-examples/`: `sfx-plan.example.json` (the 27/09 SFX list as anchors), `takes.example.json`, `adjust.example.json`,
`caption-pairs.vi.json` (94 Vietnamese hard pairs + 4 soft pairs from the ProfitBase script).

## One full run (order)

```
# 04 capture script + G0
python scripts/capture/capture_log_to_edit.py draft --feature-map feature-map.yaml --out capture-script.draft.yaml   # fill VO, values
python scripts/capture/capture_log_to_edit.py lint --script capture-script.yaml --web-data footage/web-data.md        # G0 must PASS
# 05 E0 + macro capture
python scripts/capture/e0_gate.py --config project.json --motion 10          # scroll the page during the 10 s
python scripts/capture/clean_js.py --config project.json --with-helpers      # paste footage/sdv-clean.js after every reload
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/capture/keepawake.ps1
python scripts/capture/rec.py R01-boms_t1 --config project.json              # per shot: rec -> 1 JS macro -> create footage/STOP_R01-boms_t1
python scripts/capture/ingest.py R01-boms t1 --config project.json < packed.txt
python scripts/capture/vcheck.py footage/R01-boms_t1.mkv --sheet
# 06 VO
python scripts/vo/gen_tts.py --config project.json
python scripts/vo/measure.py --config project.json
python scripts/vo/asr_check.py vo/raw/wav/*.wav                               # paid; then gen_var.py + takes.json + select_takes.py + measure.py
python scripts/vo/assemble.py --config project.json                          # edit vo/adjust.json until fit.json is OK
python scripts/vo/align.py --config project.json
# 07 music grid
python scripts/music/fit_beat_grid.py music/source.wav                       # write music.arrangement
python scripts/music/conform_music.py --config project.json
python scripts/music/check_grid.py --config project.json
# 08 build (write comp/data/cuts.json by hand from the capture log / vcheck notes)
python scripts/capture/capture_log_to_edit.py build --script capture-script.yaml --log footage/capture-log.jsonl --markers footage/markers.txt --out comp/data
python scripts/build/cut_clips.py --config project.json
python scripts/build/erase_pointer.py --config project.json e01 e02 ...
python scripts/build/make_captions_js.py --config project.json
# 09 mix
python scripts/audio/build_mix.py --config project.json
python scripts/qa/check_sfx.py --config project.json
# 10 QA + 9:16 + deliver (render with the engine, see engine/ docs)
python scripts/qa/check_numbers.py --config project.json
python scripts/qa/contact_sheet.py renders/draft.mp4 --step 1 --out renders/qa
python scripts/qa/check_shots.py renders/draft.mp4 0.3 --out renders/qa
python scripts/build/build_916.py --config project.json && python scripts/qa/check_layout_9x16.py comp-9x16/index.html
python scripts/audio/make_srt.py --config project.json
python scripts/qa/check_loudness.py deliver/final.mp4 --w 1920 --h 1080 --fps 30
```

## project.json key reference (defaults in brackets; full example: `project.example.json`)

| key | used by | meaning |
|---|---|---|
| `project` | make_srt | name of the .srt |
| `paths.{footage_dir, markers, capture_log, capture_script, web_data, vo_dir, script_txt, music_src, sfx_plan, comp_dir, comp_916_dir, deliver_dir, qa_dir, stems_dir}` | all | folders/files, relative to project.json (defaults in lib/config.py `DEFAULT_PATHS`) |
| `capture.{monitor_idx [0], max_seconds [900], frame [1920,1080], crf [14], preset, crop_top [70], source_capture}` | rec, vcheck, e0_gate, track_pointer | capture settings; crop_top = measured debugger bar height |
| `capture.prefill.{labels, expand, probe}` | (browser) `__sdvFillByLabels` | off-camera demo values |
| `e0.{forbidden_apps [codex, chatgpt], motion_pass_fps [25], motion_fail_fps [10]}` | e0_gate | gate thresholds |
| `privacy.*` | clean_js | see clean_js.py docstring (label, hide_*, mask_selectors, replace_text, split_text, old_names_re, keep_re, old_rows, routes) |
| `vo.{voice, th_db [-45], gap_s [0.25], pre_pad [0.02], post_pad [0.05], min_line_gap [0.25], max_atempo [1.06], respell_file, adjust_file, takes_file}` | gen_tts, measure, assemble, select_takes | VO settings |
| `grid.{bpm, beats_per_bar [4], bars, t0 [0.25], tail_s, fps [30], drops, hard_cuts_bars, chapters[{line, id?, bars:[in,out]}]}` | assemble, conform_music, cut_clips | the bar grid = single timing source |
| `music.{source_bpm, crossfade_s [0.03], arrangement, alt_name, arrangement_alt}` | conform_music, build_mix | source bar per grid bar |
| `build.{crop ["1920:1010"], crop_y_default [70], crf [17], source_ext [".mkv"], erase_rule}` | cut_clips, erase_pointer | clip cutting |
| `captions.{max_words [4], group_max_chars [26], group_max_words [4], hard_pairs, soft_pairs, pairs_file}` | align, make_captions_js | caption grouping |
| `mix.{sfx_trim_db [-4], margin_db [3], max_extra_db [6], cap_speech_db [9], cap_gap_db [5], peak_kpi_db [-5], music_gap_db [-6], music_duck_db [-23], lufs [-14], true_peak_db [-1], drop_kick_rise_db [6], sfx_margin_db [6], group_boost}` | build_mix, check_sfx | mix math (defaults = 27/09 values) |
| `srt.min_cue_s [0.6]` | make_srt | |
| `nine_sixteen.{app [20,365,1040,547], hero [20,952,1040,440], cap_y [1450], cap_h [105], radius [28], extra_css, html_tag, html_tag_916, hero_before}` | build_916 | 9:16 layout + engine anchors |
| `numbers.derived {"123": "formula"}`, `qa.index_html` | check_numbers | numbers allowed without web-data |

## Evidence (this session, 28/09/2026, synthetic data in a scratch folder; no paid API, no render)

| what ran | key output |
|---|---|
| capture tests | `test_capture_log_to_edit.py` PASS 21/21 · `test_v3_patch.py` PASS 10/10 · `test_review_fixes.py` PASS 5/5 · `test_log_shape.py` PASS 5/5 · `test_clean_js.py` PASS 18/18 (headless Chromium, synthetic page) |
| `capture_log_to_edit.py build` on a COPY of the real 27/09 log + script | the 27/09 code crashed (`TypeError: list indices must be integers or slices, not str` - bbox logged as a list); fixed version: `build: {"cursor": 136, "camera": 49, "highlight": 7, "privacy": 0, "footage": "1920x1010"}`, picks takes t5 / t2 (the takes PROGRESS marked PASS) |
| `rec.py SMK_t1 -t 4 --test-src "testsrc2=size=1920x1080:rate=60"` | `DONE SMK_t1 exit=0 … dup=0 drop=0` + `rec_start`/`rec_stop` lines |
| `vcheck.py … --sheet` / `motion.py … 0 4` / `flash.py` | `"size": "1920x1080", "unique_fps": 60.0, "kf_gap_max": 1.0` · `frames=239 changed=239 -> 60.0 fps` · `hits []` |
| `e0_gate.py --motion-file` (60 / 12 / 5 changes/s / static clip) | PASS 60.0 · WARN 12.2 (HOLD) · FAIL 5.3 · FAIL no motion; live APPS + CHROME checks ran on the dev machine |
| `ingest.py` / `marker.py` / `keepawake.ps1 -Minutes 0` / `fg.ps1` / `win.ps1` | 3 lines ingested (readback ok true/false) · marker lines written · `keepawake done` · ran |
| `clean_js.py --config project.example.json --with-helpers` | 15.7 kB block, `node --check` OK |
| `tts_vn.py --fake-tts` | `OK … voiceover.wav (7.22s, 24000 Hz) + captions.json (24 tu, source=estimate)` |
| `gen_tts --fake-tts → measure → select_takes → assemble → align --asr none` | `voiceover.wav 11.61s` · `OK 1 sentences use a variant take` · `diff_words 0 | group diff 0` |
| `conform_music → check_grid` (synthetic 124 BPM click, 6 bars) | `KICK KPI: 6 downbeats · max|delta| 1.6 ms (tol 40) · FAIL 0` |
| `make_captions_js → make_srt` | `captions.js: 8 groups, 24 words` · `SRT PASS` |
| `cut_clips` (testsrc take, 2 clips, crop_y 70 and 0) | `c1 OK … dur 5.833/5.806 … HOLD 3.06` · `cuts.js + 2 <video> tags written` |
| `erase_pointer --probe` | `c1: frames 175 · with pointer 15 · still orange after fill 0` |
| `build_mix` (fake VO, conformed click music, 4 synthetic SFX, alt arrangement) | `KPI I=PASS · TP=PASS · peak=PASS · speech_cap=PASS · drops=PASS · length=PASS`, `MUSIC CHOSEN: music-grid-intro.wav` |
| `check_sfx` / `check_numbers` / `check_loudness` / `check_shots` / `contact_sheet` | 3 hits reported (below +6 by design of the synthetic SFX) · `numbers 1 | not traceable 0` · 5/5 PASS on a muxed mp4 · ran · 1 sheet |
| `build_916 → check_layout_9x16` | 6/6 PASS (top gap 365 / bottom 365) |
| `python -m py_compile` all 42 .py · `node --check` 2 .js · .ps1 ASCII check 3 files | all OK |

**Not run here:** real VieNeu inference (gen_var, vieneu_worker), whisper / gpt-4o calls (align `--asr whisper`, asr_check, tts_vn `--align`),
live `gfxcapture` recording through rec.py / e0_gate `--motion`, build_mix on the real ProfitBase stems, track_pointer, any render.
`check_v3.py` of the case (ban-list + DOM numbers + caption diff + overlay layout via Playwright) was **not shipped**: it is wired to the
case's own DOM ids, a local Chrome binary path and case-specific banned phrases; `qa/check_numbers.py` + `audio/make_srt.py` +
`vo/align.py` cover numbers and caption text.
