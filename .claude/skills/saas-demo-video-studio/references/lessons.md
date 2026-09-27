# Lessons — 15 bài học trả giá thật (ca ProfitBase 26–28/09/2026)

Mỗi dòng: chuyện gì xảy ra → luật rút ra → nằm ở đâu trong pipeline.

| # | Chuyện gì xảy ra | Luật | Ở đâu |
|---|---|---|---|
| 01 | Dựng cả phim theo brief chữ, khách chê gu → dựng lại; mỗi vòng 50–66 phút | Chốt GU trước: storyboard (U1) + khung tĩnh/cảnh thử (U2) trước khi dựng hết | 03, 08 |
| 02 | Reel khách gửi là talking-head + card, không phải quay màn hình | Học NHỊP (1 ý/shot, mượt trong khung); con trỏ/zoom theo quy ước Screen Studio | taste §1 |
| 03 | Con trỏ ảo tween theo 13 điểm thưa lệch tới 155 px | Toạ độ từ capture log bbox mỗi thao tác (hoặc track dày 30 fps) | 04, 05, 08 |
| 04 | Cổng "0 px" so dữ liệu với chính nó | Hỏi "script đọc cái gì?"; vị trí con trỏ/chip kiểm bằng crop + mắt | qa-gates G5b |
| 05 | `data-duration` thay toàn cục → b-roll phủ cả phim; animate `<video>` vô tác dụng | `data-duration` từng phần tử; animate `.vwrap` | engine |
| 06 | Render biến thể bằng cách sửa tạm `index.html` → race ghi đè | 1 người ghi 1 file; 9:16 = thư mục dự án riêng | 10 |
| 07 | SFX +6,4 dB stereo nhưng +3,4 dB mono; 2 agent đo 2 định nghĩa | margin = min(stereo, mono), công thức in đầu script | 09 |
| 08 | 9:16 crop dọc cắt chữ | 9:16 màn hình dày chữ = CHIA ĐÔI | 10 |
| 09 | Lộ vendor AI + mục admin; nút "chat mới" không tạo phiên mới | Privacy mặc định CHE (không đợi khách nhắc); soát cả khung chat | 02, 05 |
| 10 | Full render 1080p ~5 phút × 3–6 lần/vòng + reviewer tuần tự | Sửa = render đoạn 720p; full 1 lần; reviewer song song; sheet 1 fps ở phiên chính | 10 |
| 11 | 5 vòng dựng, 7 lượt reviewer tuần tự, 9:16 làm 3 lần, chốt gu muộn → cả ngày | Storyboard trước · skeleton + taste mặc định · agent song song · 9:16 cùng lúc 16:9 | toàn pipeline |
| 12 | 9:16 chia đôi dồn lên trên, đáy trống ~400 px | Căn giữa dọc, đo bằng `check_layout_9x16.py` (\|trên − dưới\| ≤ 80 px) | 10 |
| 13 | Gói chia sẻ thiếu file phụ thuộc ngoài thư mục skill; đường dẫn máy cá nhân trong template | Liệt kê mọi phụ thuộc; grep đường dẫn máy trước khi phát hành; con số đếm bằng lệnh | repo này |
| 14 | Quay không kịch bản → dò con trỏ bằng màu, đoán zoom, cắt 1 cảnh thành 3, gõ nhầm 909% phải gõ lại | KỊCH BẢN QUAY CHI TIẾT + cổng G0 trước khi quay; giá trị demo chốt sẵn | 04 |
| 15 | 65 phút quay hỏng vì MÔI TRƯỜNG (agent AI khác gắn Chrome, Chrome bị che giảm vẽ, tab nền) | Cổng E0 kiểm bằng lệnh; MACRO MODE 1 lệnh JS/shot; kiểm privacy dồn cuối ca | 05 |

## Gotcha kỹ thuật ngắn

- gfxcapture/gdigrab: Chrome thường chỉ vẽ 25–45 khung đổi/s dù quay 60 fps → master 30 fps.
- Thanh "đang gỡ lỗi trình duyệt" của extension cao 70 px (ca mẫu) → `crop_top` đo 1 lần, mọi shot cùng số; thanh bật/tắt giữa shot = retake.
- Toạ độ ảnh chụp extension ≠ toạ độ khung quay (tỉ lệ dpr/CSS) → luôn quy đổi bằng `viewport_origin_px` + `dpr`, kiểm 1–2 điểm trên khung thật.
- `will-change: transform` làm Windows Graphics Capture đứng hình → không dùng khi quay.
- Macro mode trên app KHÔNG dùng React: native setter có thể khác → CHƯA KIỂM.
- `drawtext` của ffmpeg trên Windows cần `fontfile` tường minh.
- Renderer lỗi headless shell → `PRODUCER_HEADLESS_SHELL_PATH`.
- Lệnh `hyperframes render` có thể bị bộ lọc an toàn của agent con chặn ("interfere with workloads") → chạy render ở phiên chính.
