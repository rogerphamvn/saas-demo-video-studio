# 09 · SFX + mix + master −14 LUFS + .srt (agent `sdv-audio-mix`)

**Input:** `<comp>/data/grid.json`, `data/cuts.json`, `data/captions.js`, `assets/audio/{vo.wav,music-grid.wav}`, thư viện SFX
`assets/audio/sfx/*.wav`, `data/sfx-plan.json` (mỗi dòng: slot · neo `t` / ô / drop / đầu clip / từ VO · offset · file · rel_db · kind).

```bash
python scripts/audio/build_mix.py --config project.json   # luật từ-nóng, duck nhạc, SFX margin, master lặp tới -14 LUFS -> mix.m4a + mix-report.txt
python scripts/audio/make_srt.py --config project.json    # .srt từ đúng các cụm caption đang hiện trên hình
python scripts/qa/check_sfx.py --config project.json --target 3   # cổng v3 = +3 dB (mặc định của script là 6 = gu v1)
```

**Output:** `<comp>/assets/audio/mix.m4a`, `mix-report.txt`, `deliver/<name>.srt`.

**Cổng G6/G7 (script tự in KPI, exit 1 nếu FAIL):** SFX ≥ +3 dB trên nhạc (min stereo/mono) · peak ≤ VO −5 · dưới lời ≤ VO −9 ·
drop |Δ| ≤ 20 ms · −14 ±0,5 LUFS · TP ≤ −1 dBFS · độ dài = video ±0,05 s · SRT diff chữ 0, 0 cue < 0,6 s, 0 chồng cue.
