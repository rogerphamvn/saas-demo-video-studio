# 07 · Nhạc nắn theo lưới BPM (agent `sdv-audio-mix`, song song với 05)

**Input:** file nhạc (thư viện/khách; sinh mới chỉ khi người dùng duyệt chi phí), `vo/voiceover.wav`, `vo/placements.json`,
`project.json` (BPM, số ô, t0, đuôi, drop, arrangement ô nguồn → ô lưới, ô cắt cứng).

```bash
python scripts/music/fit_beat_grid.py <music.wav> --min-bpm 100 --max-bpm 130   # đo BPM + beat0 của nguồn
python scripts/music/conform_music.py --config project.json   # nối nguyên ô tại downbeat, xf 30 ms -> music-grid.wav, grid.json/.js, vo.wav dịch t0
python scripts/music/check_grid.py --config project.json > grid-check.txt
```

**Output:** `<comp>/assets/audio/music-grid.wav`, `<comp>/assets/audio/vo.wav`, `<comp>/data/grid.json`, `<comp>/data/grid.js`.

**Cổng G2:** mọi downbeat |Δ| ≤ 40 ms (đo trên FILE RA + cột đối chứng nguồn); liệt kê mối nối để người dùng nghe.
