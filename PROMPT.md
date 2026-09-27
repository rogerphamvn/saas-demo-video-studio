# PROMPT — video review web app bằng 1 prompt

Dán vào Claude Code (mở ở gốc repo này, hoặc ở dự án đã copy `.claude/` + `pipeline/` + `scripts/` + `engine/`):

```
Làm video review cho <URL>
- Sản phẩm: <1 câu: là gì, cho ai>
- Loại: B (tour 60–80 s)            # A 30–45 s 1 chức năng · B tour nhiều chức năng · C website/landing · D hướng dẫn · E 9:16 ngắn
- 3–5 chức năng đắt nhất: <tên + URL>, <…>
- Trang CẤM quay: /admin, /settings/billing
- Được tạo dữ liệu demo "Demo · …" trong tài khoản: có / không
- Giọng: VieNeu <tên giọng>          # nghe thử 1 câu trước khi chốt
- Màu brand: #6952E0 · CTA cuối: "<Tên>. Sắp ra mắt tháng 10."
- Nhạc: dùng file <đường dẫn> / thư viện có sẵn / cho phép sinh (duyệt chi phí)
- Xuất: 16:9 + 9:16 + .srt
Dùng skill saas-demo-video-studio: lên PLAN, chạy agent song song, dừng ở 3 cổng U1 · U0 · U2.
```

Chỉ `Làm video review cho <URL>` cũng chạy được: agent tự hỏi phần còn thiếu trong MỘT lượt (bước 01).

## 3 cổng người dùng

| Cổng | Agent dừng và chờ | Bạn trả lời |
|---|---|---|
| **U1 — chọn storyboard** | 3 storyboard A/B/C (khác bố cục + nhịp, cùng số liệu) + ≤ 6 câu hỏi quyết định kèm mặc định | `B` (hoặc `B, câu 2 = A`) |
| **U0 — sẵn sàng** | trước khi quay: đóng app AI khác, để Chrome đã đăng nhập, **không đụng chuột/phím** tới khi agent báo xong | `sẵn sàng` |
| **U2 — duyệt stills + cảnh thử** | 1 khung tĩnh/chương + cảnh thử 15–20 s | `ok` hoặc góp ý kiểu đạo diễn: `E4 ô 12: zoom chậm lại` |

## Bỏ qua cổng bằng mặc định

Thêm vào prompt:

```
storyboard: auto          # bỏ U1: lấy storyboard đề xuất + mặc định của mọi câu hỏi
duyệt U2: auto            # bỏ U2: dựng hết, bạn chỉ xem bản nháp cuối
sẵn sàng                  # CHỈ viết khi máy đã để yên từ lúc gửi prompt; agent vẫn chạy cổng E0 trước shot đầu
```

U0 không bỏ được hẳn: quay trong lúc máy đang bị dùng (hoặc có agent AI khác gắn vào Chrome) sẽ ra 1–5 khung/s — ca mẫu mất
65 phút vì vậy. Agent vẫn kiểm môi trường E0 bằng lệnh và dừng nếu không đạt.

## Bạn nhận được

`deliver/final-16x9.mp4` · `deliver/final-9x16.mp4` · `deliver/<tên>.srt` · `deliver/QA-REPORT.md` (số đo từng cổng: loudness,
số khớp web, privacy, lưới nhạc, bố cục 9:16) · danh sách dữ liệu demo đã tạo trong tài khoản (bạn tự quyết giữ/xoá).
