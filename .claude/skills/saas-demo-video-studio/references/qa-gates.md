# QA gates — nghiệm thu bằng PHÉP ĐO

> Trước khi tin một cổng, hỏi: **"script này ĐỌC cái gì?"** Một cổng so dữ liệu với chính nó luôn xanh (ca mẫu: cổng con trỏ
> "0.0 px trên 1571 khung" so tip với điểm dừng sinh ra từ CHÍNH track đó — xanh nhưng không chứng minh hình).
> Lệnh cụ thể của từng cổng nằm trong `pipeline/NN-*.md` tương ứng. Số đo ví dụ = ca ProfitBase.

| # | Cổng | Ở bước | Đạt khi | Đọc gì / KHÔNG đọc gì | Ca mẫu |
|---|---|---|---|---|---|
| G0 | Kịch bản quay | 04 | `G0 PASS`: mọi shot đủ trường; mọi `expected_on_screen` + `highlight.text` có nguyên văn trong web-data; không trang cấm; không bấm `never_click`; zoom trong giới hạn; bước chọn dữ liệu cũ nằm NGOÀI khoảng ghi | đọc YAML + web-data; KHÔNG mở web (selector sai chỉ lộ lúc quay) | 18 shot PASS; thêm "909%" → FAIL |
| E0 | Môi trường quay | 05 | 0 app AI khác · 4 cờ Chrome · tab visible · motion gate ≥ 25 khung đổi/s | đọc tasklist, command line Chrome, số khung đổi thật | gate 26,1 khung đổi/s sau khi sửa |
| G1 | VO + caption | 06 | whisper `matched_ratio ≥ 0.8`; nối chữ caption == script (diff 0 từ); 0 cụm 1 từ; 0 cặp từ ghép bị tách | đọc ASR vs script; KHÔNG chấm chất lượng giọng (chọn bằng tai) | 13 dòng / 27 câu, ratio 0,873, diff 0 |
| G1b | Phát âm | 06 | 2 ASR khác nhau (whisper-1 + gpt-4o-transcribe) đều nghe đúng từ khó; sai → đổi phiên âm INPUT TTS, không đổi chữ script | đọc text 2 ASR; tai người là trọng tài cuối | 8/27 câu phải đổi take |
| G2 | Lưới nhạc | 07 | mọi downbeat (kick) \|Δ\| ≤ 40 ms so lưới; drop có bước năng lượng rõ | detector kick băng 40–110 Hz trên FILE RA, cột đối chứng trên nguồn | 41/41 ô, max 21,8 ms |
| G3 | Số khớp web | 08 | mọi số trên hình có trong web-data (0 không truy được) | đọc markup + `data-num`; KHÔNG thấy số JS sinh lúc chạy | 48/48 số có trong web-data |
| G4 | Privacy | 05 + 08 | sheet 0,5 fps cuối ca quay + sheet 1 fps bản render: 0 email/tên tài khoản/mục admin/dữ liệu cũ/tên model AI | mắt người trên sheet; script chỉ bắt được thứ có màu đặc trưng | lời chào in tên tài khoản bị bắt ở sheet → vá script theo node |
| G5 | Con trỏ thật không lộ | 08 | chấm con trỏ của extension đã xoá (erase) — còn ≤ vài khung và nằm ngoài vùng đọc | detector màu cam trên clip đã cắt | còn 6 khung ở 1 clip, chấp nhận |
| G5b | Con trỏ ảo / chip đúng chỗ | 08 | crop quanh MỖI click: tip/chip nằm trên nút đang thao tác, lệch ≤ 8 px | mắt người; toạ độ từ capture log (không đoán) | — |
| G6 | SFX | 09 | mọi hit ≥ +3 dB trên nhạc (min stereo/mono); peak ≤ VO −5 dB; dưới lời ≤ VO −9 dB; drop \|Δ\| ≤ 20 ms | đọc stem trước master | script tự in KPI PASS/FAIL |
| G7 | Loudness + container | 10 | −14 ±0,5 LUFS, true-peak ≤ −1 dBFS, audio = video ±0,1 s — trên TỪNG file giao | đọc file GIAO (renderer encode lại audio) | v1: −14,1 LUFS / −1,8 dBFS; v3: −14,3 LUFS |
| G8 | Nhịp | 08/10 | cắt cứng toàn khung ≤ 6; khoảng lặng sự kiện ≤ 2,5 s | `check_shots` chỉ đếm cắt cứng (morph/camera không tính) → dùng thêm `FX_LOG` của engine | — |
| G9 | Sheet 1 fps | 08/10 | không có: khung trống/đen, chữ cụt mép, b-roll phủ phim, badge nháp, 2 nhãn mâu thuẫn trong 1 khung | mắt người — phiên chính xem SAU MỖI render, trước reviewer | bắt được mosaic trống, b-roll phủ, 9:16 cắt chữ |
| G11 | Bố cục 9:16 | 10 | \|trống trên − trống dưới\| ≤ 80 px; app/hero cùng x/rộng; caption đáy ≤ 1670 | đọc biến CSS `--app-*`, `--hero-*`, `--cap-*` | 365/365 PASS; bố cục bị chê → FAIL 165 px |
| G10 | Reviewer độc lập | 10 | agent reviewer tự đo lại G0–G11, ≥ 3 phản biện, ghi gap; KHÔNG sửa | xem `.claude/agents/sdv-reviewer.md` | — |

## Lỗi thật đã gặp (triệu chứng → sửa)

1. **B-roll phủ cả phim** — thay `data-duration` toàn cục → chỉ đặt cho `#root` và `#mix`.
2. **`opacity/scale` trên `<video>` vô tác dụng, clip giữ khung cuối** → animate wrapper `.vwrap`, ẩn ở `t + d`.
3. **Race khi render biến thể bằng cách sửa tạm `index.html`** → 9:16 là THƯ MỤC dự án riêng (2 composition cùng thư mục → lint `multiple_root_compositions`).
4. **SFX đủ to stereo nhưng chìm mono** → margin = min(stereo, mono), công thức in ở đầu script.
5. **Con trỏ ảo lệch tới 155 px** khi tween theo 13 điểm thưa → lấy toạ độ từ capture log bbox (hoặc track dày 30 fps).
6. **Zoom trên `#root` không phóng dialog/portal** → zoom trên `body`.
7. **Bắt cửa sổ theo HWND đứng hình** khi thanh debugger bật/tắt → quay monitor 0 + ping extension trước rec.
8. **Khung đầu 1920×1079 (số lẻ) → x264 từ chối** → crop chẵn + pad trong lệnh quay.
9. **`-t 150` quá ngắn** cắt mất bước cuối → mặc định 900 s, dừng bằng file STOP.
10. **Lời chào in tên tài khoản** (React tách 5 text node) → thay chữ theo node, không theo chuỗi.
11. **Nút "cuộc trò chuyện mới" không tạo phiên mới** → phía trên lộ chat cũ → xoá lịch sử OFF-CAMERA hoặc crop từ câu hỏi mới trở xuống.
12. **Cùng 1 số, 2 nhãn khác nhau trong 1 khung** (nhãn app vs nhãn cử chỉ) → không để 2 nhãn cùng khung; kiểm bằng sheet.
13. **Chrome-headless-shell cache hỏng** → env `PRODUCER_HEADLESS_SHELL_PATH=<đường dẫn chrome-headless-shell.exe>`.
14. **ffmpeg `drawtext` crash trên Windows** khi thiếu `fontfile` → truyền font tường minh.
15. **Whisper nội suy số đọc thành chữ ở 0 ms** → căn TỪNG câu (file theo dòng) + cộng offset; strict ratio 0.8.

## Tốc độ vòng sửa
- Sửa → render ĐOẠN đang sửa ở 720p; full 1080p đúng 1 lần cuối (~5,5 phút/bản trên laptop 8 luồng không GPU rời).
- Reviewer chạy SONG SONG trên phần đã ổn trong lúc builder sửa phần lỗi; gom lỗi vào 1 lần sửa.
- Khung tĩnh (still) mỗi chương bằng Playwright seek thay cho render khi duyệt bố cục.
