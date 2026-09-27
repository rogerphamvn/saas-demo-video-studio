# Chi phí · token · thời gian — SỐ ĐO THẬT (1 ca, 1 máy)

> Ca mẫu: ProfitBase (SaaS tính lãi/lỗ lô hàng, tiếng Việt), 26–28/09/2026. Máy: laptop Windows 11, CPU 4 nhân/8 luồng,
> GPU tích hợp (không GPU rời). Số nào chưa đo ghi **CHƯA ĐO** — đừng biến ước lượng thành cam kết với khách.

## 1. Bản v1 (26/09) — đường cũ: quay 1 phiên không kịch bản, dựng theo câu VO

| Hạng mục | Số đo |
|---|---|
| Video giao | 16:9 68,5 s, −14,1 LUFS, đỉnh −1,8 dBFS — khách DUYỆT |
| Credit AI (Magnific) | 2.980 = nhạc 76 s 1.520 · 23 SFX ~160 · 4 b-roll Kling 1080p 5 s 1.300 (325/clip) |
| Giọng đọc | VieNeu local: 0 đ. Gemini TTS free tier: 429 liên tục → không dùng |
| Token agent (10 lượt đầu) | 3.498.017 (builder 2.385.386 · reviewer 1.112.631), 610 tool call |
| Thời gian agent cộng dồn | 13 lượt = 373 phút (~6,2 giờ), không trừ phần chạy song song |
| Phiên quay | 495,5 s (~8,3 phút) — người dùng không đụng máy; chuẩn bị Chrome ~2 phút |
| Render full 1080p | ~4,5–5,5 phút/lần (5m29s đo 1 lần); mỗi vòng sửa 3–6 lần render + reviewer tuần tự ⇒ 50–66 phút/vòng |
| Lịch | 1 ngày làm việc (VO sáng → quay 10:55 → nháp 14:15 → cảnh thử 15:30 → FINAL ~18:20) |
| Khách nói | "người ta làm có 30' thôi, lần sau làm nhanh hơn nhé" |

## 2. Bản v3 (27–28/09) — đường MỚI của repo này: storyboard → lưới BPM → kịch bản quay → macro capture → dựng song song

| Hạng mục | Số đo |
|---|---|
| Video giao | 16:9 81,2 s, −14,3 LUFS + .srt; 9:16 render xong 28/09 00:00 — khách chấm 16:9 **7/10** ("thiếu motion graphic/3D/flip") |
| Credit AI | nhạc: 0 (nắn bài cũ theo lưới 124 BPM, 41/41 downbeat, max \|Δ\| 21,8 ms); SFX dùng lại thư viện v1 |
| VO | 13 dòng / 27 câu VieNeu: sinh 150 s (nạp model 44 s); 8 câu đổi take sau kiểm phát âm 2 ASR; ratio 0,873, diff chữ 0 |
| Quay — lượt 1 | 65 phút → chỉ ~70% một shot (môi trường hỏng: agent AI khác gắn Chrome, Chrome bị che giảm vẽ) ⇒ sinh ra cổng E0 |
| Quay — sau E0 | Ca 1: 7 shot, sổ ca ghi ~14 phút (từng bước, ~13,9 lượt gọi/shot) · Ca 2+3: 10 shot, sổ ca ghi 17 phút (MACRO, ~7,6 lượt/shot) → 18 file shot. Mốc giờ nhật ký rộng hơn vì gồm chuẩn bị/reset: Ca 1 21:56→22:17, Ca 2+3 22:17→22:46 |
| Render full (HyperFrames 0.8.78, 3 worker) | 16:9: 11m38s · 9:16: 12m56s (cho 81,2 s video; chụp khung chiếm ~2/3) |
| Token agent v3 | **CHƯA ĐO** (không ghi sổ ở ca này) |
| Lịch v3 | quay Ca 1 từ ~21:56 → Ca 2+3 xong 22:46 → 16:9 giao 23:47 (dựng chạy song song với quay) |

## 3. Mục tiêu "1 prompt ~30–45 phút tới bản nháp"

**CHƯA ĐO.** Đây là mục tiêu thiết kế của repo (storyboard + agent song song + macro capture + render đoạn), chưa có ca nào bấm
giờ trọn từ prompt tới bản nháp. Ca đầu tiên chạy theo repo PHẢI bấm giờ từng bước (điền bảng dưới) và gửi lại số.

| Bước | Ước lượng thiết kế | Đo được |
|---|---|---|
| 01 brief + 02 recon | 5–10 phút | |
| 03 storyboard ×3 + U1 | 10 phút + chờ người dùng | |
| 04 kịch bản quay + G0 | 5–10 phút | |
| 05 E0 + quay macro | ~1,7 phút/shot + 5 phút cổng | |
| 06 VO + 07 lưới nhạc (song song với 05) | 5–10 phút | |
| 08 dựng song song + still + U2 | 20–40 phút + chờ | |
| 09 mix + 10 render 2 bản + QA | 15–30 phút (render ~12 phút/bản ở 81 s) | |

## 4. Công thức báo giá gợi ý (khách tự điền đơn giá)
- Chi phí biến đổi = credit AI (nhạc/SFX/b-roll, có thể = 0 nếu dùng thư viện) + phút ASR whisper (~1–2 phút audio) + token agent.
- Chi phí thời gian người dùng = chuẩn bị Chrome (~2 phút) + để máy yên lúc quay (~30 phút cho ~18 shot) + 2–3 lượt duyệt.
- Quy ra tiền: **CHƯA ĐO** (phụ thuộc gói credit / giá API của từng người).
