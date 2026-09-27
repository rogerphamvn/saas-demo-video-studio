# Ca mẫu: ProfitBase (26–28/09/2026) — đã làm sạch

ProfitBase: SaaS tiếng Việt tính lãi/lỗ theo lô hàng cho người bán TMĐT (dashboard, form tạo lô, định mức nguyên liệu,
so sánh lô, khuyến mãi, ngân sách marketing, chuyên gia tài chính AI). Chủ sản phẩm là tác giả repo.
Đã bỏ: footage, âm thanh, render, ảnh UI, email/tên tài khoản, id bản ghi, tên lô/SKU cũ, URL thật (→ `<your-app>`).

## Ba phiên bản và điều học được

| Bản | Cách làm | Kết quả | Bài học → pipeline |
|---|---|---|---|
| v1 (26/09) | quay 1 phiên 8,3 phút không kịch bản; dựng theo câu VO; 5 vòng dựng, reviewer tuần tự | 16:9 68,5 s −14,1 LUFS **được duyệt**; 9:16 làm 3 lần; cả ngày | cần storyboard + kịch bản quay + agent song song (LESSON-01, 11, 14) |
| v2 (26/09 tối) | "kinetic slab": slab chéo, 3D, bloom, burst | "bản mới chưa thấy ok" | quá nhiều thứ/khung, thiếu ngữ pháp nối cảnh → ban-list + 1 thứ/khung |
| v3 (27–28/09) | research ref → 3 storyboard (U1 chọn B) → lưới 124 BPM 41 ô → kịch bản quay 18 shot (G0) → E0 + macro → dựng 13 chương | 16:9 81,2 s −14,3 LUFS + .srt; **7/10** "thiếu motion graphic/3D/flip" | pipeline của repo này; motion pass v3.1 đang làm (TODO sync) |

## File trong thư mục

| File | Là gì |
|---|---|
| `capture-script.yaml` | kịch bản quay v3 thật (18 shot R01–R15, schema v3: zoom tại nguồn, `expect_value`, `rec_start` theo file, bước OFF-CAMERA) — đã thay tên lô/URL/id bằng placeholder |
| `storyboard-B.md` | storyboard "Chapter tour" khách chọn ở U1: 13 chương trên lưới 41 ô, move, cử chỉ số, SFX, cắt cứng |

## Số đo (nguồn: sổ ca, log render, file kiểm — chi tiết `references/cost-time.md`)

- Lưới: 124 BPM, ô 1,9355 s, 41 ô + đuôi 1,6 s, t0 0,25 s → 81,2 s; nhạc nắn từ bài v1: 41/41 downbeat, lệch tối đa 21,8 ms.
- VO: 13 dòng / 27 câu VieNeu; 8 câu đổi take sau kiểm phát âm 2 ASR; whisper ratio 0,873; diff chữ caption 0.
- Quay: cổng E0 fail 3 lần (agent AI khác gắn Chrome, Chrome chạy nền bỏ qua cờ, tab MCP ở nền) → PASS 26,1 khung đổi/s;
  7 shot từng bước + 10 shot macro (~7,6 lượt/shot); `crop_top` 70 px; viewport 1920×1010 @ dpr 1.
- Dựng: 18 clip thật, 13 scene; kiểm tự động: ban-list 0 hit · 48/48 số có trong web-data · caption diff 0 · 325 mẫu bố cục 0 tràn · 0 lỗi trang.
- Render: 16:9 11m38s, 9:16 12m56s (HyperFrames 0.8.78, 3 worker, laptop không GPU rời).
- Token agent v3: CHƯA ĐO.

## VO (13 dòng, bản khách duyệt) — ví dụ độ dài/nhịp, không phải để chép

E1 "Mở máy lên, bạn không nhìn số liệu — bạn nhìn tình hình. …" · E2 "Lô hàng này lãi hay lỗ? Gõ giá bán, gõ số lượng — cột bên phải
trả lời ngay khi bạn còn đang gõ." · … · E13 "ProfitBase. Sắp ra mắt, tháng mười, hai nghìn không trăm hai mươi sáu."
Toàn bộ lời đọc nằm trong cột VO của `storyboard-B.md`.
