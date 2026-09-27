# SB-B — "Chapter tour" (north-star: `ccassist-chapter-tour`, yashagl 60 s / 12 chương)

> Ví dụ THẬT (đã làm sạch) — storyboard user chọn ở cổng U1, ca ProfitBase 27/09/2026. Viết bởi agent storyboard (Opus 5.5). Chưa qua reviewer lúc viết. (Khung tĩnh PNG không kèm trong repo vì chứa UI thật.)
> Nhãn: [WD] = số đã có trong web-data; [CHỜ …] = số chưa đo, dựng bằng ô xám cho tới khi đo. Lưới: 124 BPM, ô 1,935 s, 41 ô.

## 1. Ngữ pháp thị giác SB-B

| Luật | Giá trị |
|---|---|
| Cảm xúc | Rõ ràng, "đi tour sản phẩm" — người xem luôn biết đang ở chương mấy, tính năng gì; tin vì thấy UI thật |
| Bố cục | **cột trái 640 px cố định**: "0X / 13" + tiêu đề 2 dòng 76 px (Inter 900 + Plex Serif nghiêng tím) · **phải: UI thật trong card bo 22 px** ~760–1020 px |
| Chữ | tiêu đề chương là chữ to nhất khung ngoài caption; **ở lại suốt chương** (khác plan §4 "thu về góc 28 px") — đổi được nếu anh muốn đúng plan |
| UI | card crop 1 thành phần (nguyên trang chỉ E12); thẻ chú thích số **bật ra từ mép card** (kiểu tooltip nổi yashagl) thay vì chiếm cả khung |
| Nối cảnh | tiêu đề cũ trượt lên-ra, mới vào clip-mask 1 phách sau downbeat (m7); card morph đổi kích thước (m6); Chip Đơn chạy dưới card |
| Cắt cứng | **4** (ô 17 E5→E6 · ô 23 E7→E8 · ô 33 E10→E11 · ô 39 E12→E13) — đều ở chỗ đổi route |
| Nhịp sự kiện | vừa: 1 sự kiện/2 phách; **khoảng lặng dài nhất ≈ 1,5 s** |
| Màu | nền #F4F3EF lưới 30%; tím ở tiêu đề + viền highlight; xanh/đỏ chỉ số lãi/lỗ; tối chỉ E13 |
| UI thật trên hình | ≈ **30,5/41 ô = 74%** (sát trần 75%) · nguyên trang ≈ 3 ô = 7% |

## 2. Bảng 13 chương

| Ch | Ô (s) | VO | Tiêu đề 2 dòng | Khung hình (trái = tiêu đề · phải = card UI) | Move | Cử chỉ số | SFX | → chương sau | UI ô |
|---|---|---|---|---|---|---|---|---|---|
| E1 | 0–3 (0–5,8) | "Mở máy lên, bạn không nhìn số liệu — bạn nhìn tình hình…" | 01 · Mở máy ra, / *nhìn là biết.* | card Dashboard (4 thẻ KPI + chart + Top 5); bấm "Quý này" **đúng DROP 1 (ô 3)**; Chip Đơn nghiêng nhẹ nhấc khỏi hàng "Demo · Lot A"  | m7 · m3 · m1 | 4 thẻ odometer cùng đổi [CHỜ R10] | click · counter · chime ô 3 | tiêu đề trượt ra, card morph thành 2 thẻ Global/Local | 2 |
| E2 | 3–7 (5,8–13,5) | "Lô hàng này lãi hay lỗ? Gõ giá bán, gõ số lượng…" | 02 · Lô này lãi / *hay lỗ?* | Chip đáp nút "Chọn Local" → flip 3D (duy nhất) → card form (ô Giá bán + Số lượng) cạnh cột "Kết quả P&L" | m1 · flip · m6 | cột phải nhảy từng phím → **chỉ 26.970.000** [WD] (v3.3) | flip · typing | card cuộn xuống khối COGS (trong card, không cắt) | 3,5 |
| E3 | 7–10 (13,5–19,4) | "Giá vốn bóc tới từng khoản… khung tranh tám mươi hai nghìn." | 03 · Giá vốn, / *bóc tới từng khoản.* | card crop khối "Cấu thành COGS"; dòng "Khung tranh 40×60cm 82000" thêm vào; dòng cũ mờ | m9 · m3 | Tổng COGS 307.872 [WD] | typing · pop-1 · counter | card morph sang cột phải (BEP / Thu hồi) | 2,5 |
| E4 | 10–14 (19,4–27,1) | "Hoà vốn ở đơn thứ chín… bao nhiêu thật sự về túi." | 04 · Bán một đơn, / *về túi bao nhiêu?* | card UI thật (BEP 9 · Thu hồi 13 · khối Tiền chạy — frame s03b) viền tím quanh "Tiền chạy"; **thẻ chú thích bật ra từ mép trái card**: thanh ngang 899.000 bị cắn → 717.200, bóng gạch −179.800 / vạch −2.000 ; ô 13: lưới 30 chấm trong thẻ chú thích | m11 · m4 · m5 | G1–G3 [WD, CHỜ Ca 0]; nhãn "lô 30 cái" | bite (bù) · counter · dot-tick (bù) | 717.200 · 9 · 13 thu về hàng "BẰNG CON SỐ" đáy cột trái (m13), ở lại tới E5 | 2,5 |
| E5 | 14–17 (27,1–32,9) | "Chỉ livestream, bơm ads, hay chạy full marketing… nó nói thẳng: lỗ." (v3.3) | 05 · Tiêu quá tay, / *nó nói thẳng.* | card "Mô phỏng kịch bản": **3 preset** (Livestream → Bơm Ads → Full Marketing) 1 phách/cú → **gõ Ads 10 → 43** → "Lợi nhuận âm!" punch-in 1,4× + pill → **ô 17 DROP 2** cảnh báo gạch, "Lợi nhuận ròng 8.879.840 ₫" xanh; Chip đổi chấm xanh  | m11 · m1 | G5 [WD: Ads 43% → "Lợi nhuận âm! Thua lỗ 20.260 ₫"; gõ về 10] | click ×3 · stinger-1 · chime | **CẮT CỨNG #1 (ô 17)** sang /boms | 2 |
| E6 | 17–20 (32,9–38,7) | "Tự sản xuất? Khai nguyên liệu một lần… Thêm một dòng, con số tự tính lại." (v3.3) | 06 · Tự sản xuất? / *Khai một lần.* | card crop bảng định mức; "Thêm dòng" + Lưu; mũi tên cong NCC→Thành tiền→COGS vẽ trên card | m15 · m7 | COGS/sp 32.200 → 41.700 ₫ [WD] | click · diagram-1 | card tách đôi thành 2 thẻ lô (morph) | 2,5 |
| E7 | 20–23 (38,7–44,5) | "Hai lô đặt cạnh nhau…" | 07 · Hai lô cạnh nhau. / *Lô nào đáng vốn?* | card So sánh (2 thẻ lô thật, crop); chú thích nổi: bảng điểm 11 – 0, tick 5 tiêu chí | m5 · m3 | G4 11 – 0 [WD] | dot-tick ×5 · counter | **CẮT CỨNG #2 (ô 23)** sang /promotions | 2 |
| E8 | 23–27 (44,5–52,3) | "Giảm hai mươi phần trăm có lãi không?…" | 08 · Giảm 20% / *có lãi không?* | card waterfall thật; **dropdown loại KM; gõ mức giảm 20 (Lỗ -$385) → 30** → punch-in "Promo không thể hòa vốn" → **gõ 5 (Lãi: $89)** về xanh **đúng DROP 3 (ô 27)**; tên CT "Demo · Khuyến mãi 14 ngày" | m11 · m15 | G6 [WD] | chart-rise-1 · stinger-2 · chime | card co + trượt sang Marketing (morph) | 3 |
| E9 | 27–30 (52,3–58,1) | "Ngân sách marketing chia theo kênh, ra KPI nội dung, gắn đúng lô hàng đang bán." (v3.3) | 09 · Ngân sách chia kênh, / *gắn đúng lô hàng.* | card Marketing: lô đã liên kết (chọn off-camera) → NS MKT 7.600.000 ₫ · ROAS 5.26x → "Tổng kênh = 100%" → Lưu Kế Hoạch; **KHÔNG Áp dụng vào P&L, KHÔNG cảnh báo vàng**; mũi tên về Chip | m15 · m1 | tick 100% [WD] | diagram-2 · pop-2 | card thu về vùng slider ROI | 2,5 |
| E10 | 30–33 (58,1–63,9) | "Quảng cáo ROI càng cao càng tốt? Không…" | 10 · ROI cao chưa chắc / *đã ngon.* | card crop slider + "Gợi ý" (khung che "$"), kéo 6 s | m6 | vùng ngọt [CHỜ Ca 3] | whoosh-1 · chime | **CẮT CỨNG #3 (ô 33)** half-time | 2,5 |
| E11 | 33–36 (63,9–69,7) | "Cần một ý kiến? Hỏi thẳng chuyên gia tài chính AI — bằng chính con số của lô hàng bạn." (v3.3) | 11 · Hỏi thẳng / *chuyên gia tài chính.* | card Expert: skeleton → trả lời thật; macro số payback | m12 · m2 | số trong câu trả lời [CHỜ Ca 3] | typing · pop-1 | tiêu đề trượt ra, card nở thành khung montage | 2 |
| E12 | 36–39 (69,7–75,5) | "Kho, nhập hàng, KOC, dự án, trợ lý AI — tất cả trong một chỗ." (v3.3; bỏ R09 sức khoẻ SP) | 12 · Tất cả / *trong một chỗ.* | cột trái thành danh sách module sáng dần; card phải đổi footage thật mỗi phách (panel swap) | m10 · m1 | — | click mỗi phách · riser | **CẮT CỨNG #4 (ô 39)** sang nút Theme | 3 |
| E13 | 39–41 (75,5–79,4) | "ProfitBase. Sắp ra mắt, tháng mười…" | 13 · ProfitBase. / *Sắp ra mắt · 10.2026* (v3.3) | vòng tròn tối từ nút Theme; trái: lockup + hàng "BẰNG CON SỐ" 26.970.000 · 717.200 · 9 · 13 · 11 – 0 [WD]; phải: app theme tối  | m14 · m13 | 5 số tổng kết | circle-wipe (bù) · logo-hit | hết | 0,5 |

**Tự đo trên giấy:** cắt cứng **4** · khoảng lặng dài nhất **≈ 1,5 s** · UI **30,5/41 ≈ 74%** · nguyên trang **≈ 7%**.

## 3. Nhận xét sau khi XEM khung tĩnh

- Đọc được nhất: người xem luôn có "neo" (số chương + tiêu đề trái). UI thật lên hình nhiều nhất — khớp ý anh "20 màn UI thật".
- **Điện thoại:** tiêu đề 76 px → ~15 px khi xem 16:9 trên máy dọc — đọc được; chữ trong UI thật (15–19 px gốc) → 3–4 px — **không đọc được**, chỉ
  thẻ chú thích số (40 px) và caption mang nghĩa ⇒ bản 9:16 chia đôi (v3 §5) là bắt buộc cho người xem điện thoại, không phải tuỳ chọn.
- Caption 92 px + tiêu đề 76 px = 2 khối chữ lớn cùng khung : bản 92 px vẫn cân vì caption nằm dưới card, nhưng khung
  "đông" hơn bản pill; bản pill 48 px để tiêu đề là chữ to nhất — đúng ngữ pháp yashagl hơn.
- Rủi ro: UI 74% sát trần 75% — nếu Ca 1–3 quay dài hơn dự kiến, dễ vượt; ổn định nên nhàm nếu 13 chương y hệt khuôn → cần 3 drop (ô 3/17/27)
  đổi ánh nền + punch-in để phá nhịp.


> **v3.3 (27/09, Agent A vòng 2):** E2 chỉ 26.970.000 · E5 3 preset + gõ Ads 10→43→10 · E6/E9/E11/E12/E13 VO mới · E8 dropdown + gõ 20→30→5 · E9 bỏ Áp dụng/cảnh báo vàng · E13 10.2026 · G2 nhãn "−179.800 ads + thuế". 
