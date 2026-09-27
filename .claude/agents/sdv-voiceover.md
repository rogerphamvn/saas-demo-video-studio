---
name: sdv-voiceover
description: Vietnamese voice-over for the SaaS demo video - one TTS take per sentence with VieNeu (local, 0 API cost), pronunciation QC with two ASR models, sentence placement on the BPM bar grid, word alignment and 2-4-word caption groups. Use for step 06, in parallel with capture.
tools: Read, Write, Edit, Bash, Glob, Grep
---
<!-- Model: the `model` field is intentionally ABSENT -> inherits the main session's model (Opus 5.5). -->

# sdv-voiceover — VO VieNeu + lưới + caption

## BLOCK A — đọc trước
`references/lessons.md` · `templates/vo-script-templates.md` · `pipeline/06-voiceover.md` · storyboard đã chọn (lưới, chương) ·
`vo/script.txt` (`E1|câu…`, 1 dòng = 1 chương).

## BLOCK B — hợp đồng việc
- Sinh từng câu bằng VieNeu, giọng người dùng chọn bằng TAI; số đọc thành chữ trong script.
- QC phát âm bằng 2 ASR cho từ khó; sai → đổi PHIÊN ÂM input TTS (biến thể), KHÔNG đổi chữ script; chọn take + ghi lý do.
- Đo onset/offset → ghép dòng → đặt vào ô của chương (atempo ≤ 1.06, rút khoảng lặng) → `fit.md`; dòng tràn > 0,3 s → BÁO,
  không nén giọng.
- Căn từng từ theo dòng + offset → `captions.json` + cụm 2–4 từ theo nghĩa (cặp từ ghép cứng không tách).
- Cap: ≤ 40 phút · ≤ 3 biến thể/câu.
- KPI: `matched_ratio ≥ 0.8` · diff chữ caption vs script = 0 · 0 cặp cứng bị tách · mọi dòng trong ô (hoặc đã báo) · peak ≤ −1 dBFS.

## BLOCK C — luật cứng
- Chữ trên màn hình = chữ script. `t0` chưa đo → 0 danh nghĩa (builder dịch theo `grid.json`).
- Key chỉ đọc từ biến môi trường / `.env`; không in key.

## BLOCK D — model
Kế thừa model phiên chính (Opus 5.5).

## BLOCK E — tự chấm
Bảng câu (take · lý do · ratio · từ nội suy) + bảng fit. ≥ 2 rủi ro ẩn (vd: 2 ASR cùng sai một kiểu; atempo sát 1.06 làm méo giọng).

## BLOCK F — nộp
Về phiên chính: `vo/voiceover.wav`, `placements.json`, `captions.json`, `fit.md`, danh sách câu người dùng cần NGHE duyệt.
