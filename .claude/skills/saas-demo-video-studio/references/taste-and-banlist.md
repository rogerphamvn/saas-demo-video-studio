# Taste + ban-list — "gu" mặc định cho video review web app

> Đúc từ phản hồi THẬT của 1 khách (ca ProfitBase 26–28/09/2026, 3 phiên bản: v1 được duyệt, v2 "chưa thấy ok",
> v3 chấm 7/10 "thiếu motion graphic / 3D / flip") + phân tích các launch film SaaS làm tham chiếu học (không chép).
> Đây là GU MẶC ĐỊNH, không phải chân lý: khách mới vẫn chốt bằng storyboard (cổng U1) + khung tĩnh / cảnh thử (cổng U2).

## 1. Bảy câu gốc

1. **Mỗi khung nói 1 ý, phóng to đúng 1 vùng.** Bản bị chê có 4–5 lớp/khung (UI nguyên trang + 2–3 thẻ số + caption + slab).
2. **Mượt nằm TRONG khung** (morph card, vẽ đường, đếm số, settle 1.06→1), không nằm ở kiểu chuyển cảnh. Cắt cứng toàn khung ≤ 6/phim.
3. **Web app thì PHẢI có con trỏ + zoom bám điểm tương tác + minh hoạ.** Lời chê nguyên văn bản đầu: "chưa có zoom in/out,
   trỏ chuột tới, chưa chuyển cảnh mượt, thiếu hiệu ứng minh hoạ".
4. **Số trên hình là số THẬT trên web lúc quay** (file `web-data`). Không số giả, không % tự tính, không làm tròn "cho đẹp".
5. **Chọn BPM trước, mọi thứ bám lưới ô nhịp** (drop, cắt, cử chỉ số rơi đầu ô). Nắn nhạc theo lưới — không bẻ lưới theo nhạc.
6. **Mỗi số chính có 1 cử chỉ** (split-flap/odometer · thanh bị "cắn" + bóng gạch chéo · lưới chấm · bảng điểm · số khổng lồ ở drop).
7. **Clip gốc chuẩn → edit nhanh:** kịch bản quay chi tiết + capture log bbox; không "quay đại rồi sửa khi dựng".

## 2. Thông số đã được khách duyệt

| Mục | Giá trị |
|---|---|
| Bố cục 16:9 "chapter tour" | trái: "0X / NN" + tiêu đề 2 dòng (Inter 900 + serif nghiêng màu accent); phải: 1 card UI thật bo 22 px; dưới: caption |
| Caption | cụm **2–4 từ theo nghĩa**, không tách từ ghép, không cụm 1 từ; 92 px, font 900, viền tối; luôn hiện khi VO nói |
| Màu | nền trung tính sáng + **1 accent duy nhất**; xanh/đỏ CHỈ cho số tốt/xấu (lãi/lỗ); nền tối để dành cho cảnh kết |
| Zoom | tại nguồn (CSS transform lúc quay) ≤ 2.0×, giữ ≥ 1,5 s để có khung nét; camera hậu kỳ ≤ 1.5× |
| Chuyển chương | card morph / flip / push / zoom / slab / drop trên downbeat + sweep ánh sáng; ≤ 1 hiệu ứng 3D lớn/chương |
| Nhịp sự kiện | ≥ 1 sự kiện mỗi 2 phách; khoảng lặng sự kiện dài nhất ≤ 2,5 s (trừ 2 s lặng thẻ kết) |
| UI thật trên hình | 60–75% thời lượng; UI nguyên trang (> 60% khung) ≤ 25% |
| Âm thanh | master −14 LUFS, true-peak ≤ −1 dBFS; nhạc duck dưới lời; SFX ≥ +3 dB trên nhạc (đo min(stereo, mono)); không SFX đè từ nhấn mạnh nhất của câu |
| 9:16 | chia đôi CĂN GIỮA DỌC: app 1040×547 @ y 365 · hero slot cố định 1040×440 @ y 952 · caption y 1450; |trống trên − trống dưới| ≤ 80 px; camera app 1.0× |
| Giọng | chọn bằng TAI (nghe thử 1 câu), không theo điểm máy chấm |

## 3. Bộ 15 "move" (map vào chương trong storyboard, không dùng hết một lúc)

| m | Move | Ghi chú dựng (GSAP tất định) |
|---|---|---|
| m1 | Chip cầu nối (shared element) đi xuyên phim | 1 phần tử DOM, tween tới bbox trong capture log |
| m2 | Macro 1.8× → pull-back | khung quay giữ ZN 1.8× → scale 1 trong 1 s `expo.out` |
| m3 | Split-flap / odometer từng cột | chữ số nằm sẵn trong HTML lúc build; chỉ tween transform |
| m4 | Thanh bị "cắn" + bóng gạch chéo | 2 lớp; nhãn vào sau 0,3 s |
| m5 | Tick lần lượt (chấm / tiêu chí) | stagger theo phách, không nảy |
| m6 | Card morph one-take giữa chương | đổi left/top/width/height/radius 0,6 s |
| m7 | Tiêu đề 2 dòng trái + UI phải | chữ lên qua mask, trễ 1 phách sau downbeat |
| m8 | Chữ vào từng từ xám → đậm | span dựng sẵn |
| m9 | Chồng dòng, dòng cũ mờ | opacity .35 |
| m10 | Menu trái sáng dần ↔ panel phải đổi | montage module, 1 mục/phách |
| m11 | Punch-in nhanh + pill gắn vùng | 1 → 1.4× 0,5 s `power4.out` |
| m12 | Skeleton xám → nội dung thật | cho cảnh AI trả lời |
| m13 | Số lớn thu nhỏ xếp hàng đáy ("by the numbers") | `HF.strip()` |
| m14 | Vòng tròn mở từ nút vừa bấm | `clip-path: circle()` — `HF.circleWipe()` |
| m15 | Đường/mũi tên cong tự vẽ nguyên nhân → kết quả | SVG `stroke-dashoffset` — `HF.curve()` |

## 4. BAN-LIST (agent dựng gặp là sai — reviewer grep được)

1. Vòng shockwave · bụi hạt · tách RGB · rung camera · lens flare · glow neon · sàn lưới · nền nhấp nháy · chuyển cảnh iris/flash.
2. Easing nảy/đàn hồi: `back.out`, `elastic`, `bounce` (kể cả huy hiệu → dùng `expo.out`).
3. Bố cục mặc định "chữ giữa màn trên gradient, mọi thứ fade-in"; HUD microtype 4 góc + timecode.
4. Slab chéo nhiều màu, gradient bão hoà phủ phim, b-roll stock người thật (trừ khi khách chọn gu đó).
5. > 1 hiệu ứng 3D lớn/chương.
6. Số không có trong web-data, % tự tính, làm tròn.
7. Zoom hậu kỳ > 1.5× trên footage 1×.
8. Cắt cứng toàn khung > 6.
9. Kỹ thuật (HyperFrames phải tất định): `Math.random`, `onUpdate`, gán `textContent` khi timeline chạy, `filter: blur`,
   CSS transition, `opacity/filter` trên phần tử `preserve-3d` (fade wrapper), animate `<video>` trực tiếp (animate `.vwrap`).
10. Caption làm vai chính (to hơn tiêu đề chương) — trừ khi khách chọn.

Ghi chú: `engine/lib/txfx-v2.js` (gu v2 "KINETIC SLAB") có `FX.burst` (hạt) và `FX.kinetic` (`back.out`) — vi phạm mục 1–2,
chỉ dùng khi khách chọn gu v2. `engine/lib/motion-kit.js` có `burst` dạng tia ngắn ở drop — dùng tiết chế (3 lần/phim trong ca mẫu).

## 5. Lịch sử chê → sửa (để khỏi lặp lại)

| Bản | Khách nói | Nguyên nhân gốc | Sửa |
|---|---|---|---|
| v1 nháp | "chưa có zoom in/out, trỏ chuột tới, chưa chuyển cảnh mượt, thiếu hiệu ứng minh hoạ" | dựng theo brief chữ, chốt gu muộn | con trỏ ảo + camera bám điểm + spotlight; chốt gu TRƯỚC bằng cảnh thử |
| v1 9:16 | "bị cắt mất nhiều" | crop dọc 608 px phóng 1.776× | chia đôi |
| v1 9:16 lần 2 | "bố cục không cân đối giữa màn hình" | chia đôi dồn lên trên (đáy trống ~400 px) | căn giữa dọc, đo bằng `check_layout_9x16.py` |
| v1 tổng | "người ta làm có 30' thôi, lần sau làm nhanh hơn" | 5 vòng dựng, reviewer tuần tự, 9:16 làm 3 lần | storyboard + cảnh thử trước; agent song song; render đoạn 720p khi sửa |
| v2 "kinetic slab" | "bản mới chưa thấy ok" | quá nhiều thứ/khung, không có ngữ pháp nối cảnh | v3: 1 thứ/khung, lưới BPM, chương 2 dòng, chip cầu nối, cử chỉ số |
| v3 | chấm 7/10: "thiếu motion graphic, 3D, flip như ref" | lớp motion quá tiết chế | v3.1 motion pass (đang làm lúc đóng gói repo — xem README ROADMAP) |
