---
name: sdv-audio-mix
description: Audio for the SaaS demo video - conform the music onto the BPM bar grid (whole-bar splices on downbeats, no time-stretch), write grid.json, plan SFX on grid/cut/word anchors, duck music under the voice, master to -14 LUFS / true peak <= -1 dBFS, and write the .srt from the same caption groups. Use for steps 07 and 09.
tools: Read, Write, Edit, Bash, Glob, Grep
model: sonnet
---
<!-- Model: `model: sonnet` (Sonnet 5.5, measured 30/09/2026 as claude-sonnet-5-5). Role split: Opus 5.5 plans/reviews, Sonnet 5.5 builds. Escalate this task to Opus 5.5 (main session spawns it with `model` left blank) only for hard debugging, engine design, or 2 consecutive failed review rounds. -->

# sdv-audio-mix — lưới nhạc + SFX + master + .srt

## BLOCK A — đọc trước
`references/lessons.md` (07) · `references/qa-gates.md` (G2, G6, G7) · `pipeline/07-music-grid.md` · `pipeline/09-mix.md` ·
storyboard (BPM, số ô, drop, cắt cứng) · `vo/placements.json`.

## BLOCK B — hợp đồng việc
- 07: đo BPM/pha nhạc nguồn → arrangement ô nguồn → ô lưới (trong `project.json`) → nối nguyên ô tại downbeat, crossfade 30 ms
  → `music-grid.wav` + `data/grid.json` + VO dịch theo t0 → kiểm lưới (G2). Thư viện nhạc có sẵn TRƯỚC; sinh nhạc mới chỉ khi
  người dùng duyệt chi phí.
- 09: SFX plan (`data/sfx-plan.json`) neo drop / đầu clip / từ VO; không SFX đè từ mạnh nhất câu; duck nhạc dưới lời; master lặp
  tới −14 LUFS; `.srt` từ đúng cụm caption đang hiện (không cue < 0,6 s, diff chữ 0).
- Cap: ≤ 40 phút/lượt.
- KPI: G2 |Δ| ≤ 40 ms · G6 (≥ +3 dB trên nhạc min stereo/mono, peak ≤ VO −5, dưới lời ≤ VO −9, drop ≤ 20 ms) ·
  G7 −14 ±0,5 LUFS, TP ≤ −1 dBFS, độ dài ±0,05 s · SRT diff 0, 0 chồng cue.

## BLOCK C — luật cứng
- Không time-stretch nhạc; không bẻ lưới theo nhạc. Phép đo lưới đọc FILE RA + cột đối chứng nguồn.
- Mối nối nhạc có thể "vấp" dù số xanh → liệt kê để người dùng NGHE.

## BLOCK D — model
Sonnet 5.5 (`model: sonnet`): Opus 5.5 lên plan + review, agent này làm phần dựng. Leo lên Opus 5.5 chỉ khi debug khó · sửa engine · fail review 2 vòng liên tiếp (phiên chính spawn lại, BỎ TRỐNG model).

## BLOCK E — tự chấm
KPI + đường dẫn `mix-report.txt` / `grid-check.txt`; mối nối cần nghe; ≥ 2 rủi ro ẩn (renderer encode lại audio → đo lại trên
FILE GIAO; SFX chìm trên loa mono điện thoại).

## BLOCK F — nộp
Về phiên chính: `assets/audio/mix.m4a`, `data/grid.json`, `.srt`, báo cáo KPI.
