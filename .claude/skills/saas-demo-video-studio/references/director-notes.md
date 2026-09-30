# Từ điển ghi chú đạo diễn — 30 câu (địa chỉ + câu + con số)

> Dùng ở bước **sửa / nghiệm thu** (SKILL.md §4 pipeline bước 08 dựng và 10 QA; mỗi lượt sửa ở cổng U2 và sau reviewer). Đúc từ nghiên cứu ref motion 30/09/2026 (REFS-SYNTHESIS §2).
> Thông số là gợi ý xuất phát, không phải luật.
>
> **Nguồn phương pháp (đừng gán nhầm):** phép "ghi chú đạo diễn bằng ngôn ngữ camera" thuộc **6 bước của `rexan_wong`**
> (`https://x.com/rexan_wong/status/2103707054108299437`). Bài `0xMovez` (`https://x.com/0xMovez/status/2104216919033192746`) là khoá **12 bước**
> có nhúng 6 bước đó và mở rộng thêm. Bảng dưới do ta tự viết lại; không chép nguyên văn prompt hay code của tác giả nào.

Cách dùng: ghi chú **phải có địa chỉ** (`E4 ô 12`, hoặc `shot R05 t=3.2 s`) + **một câu ở bảng dưới** + **con số nếu có**. Ghi chú kiểu "mượt hơn", "sang hơn", "pro hơn" không có địa chỉ/con số ⇒ agent cãi hoặc đổi lung tung (bài 0xMovez + rexan nói cùng ý).
Cột "Độ tin": **[ĐO]** = đo trên video ref thật (ffprobe/khung hình) · **[GU]** = gu đã chốt của user (taste-profile) · **[BÀI]** = bài X nói, chưa kiểm · **[ĐX]** = researcher đề xuất.

| # | Câu ghi chú (VI) | Bản EN cho agent | Hiệu ứng tạo ra | Thông số gợi ý | Tin |
|---|---|---|---|---|---|
| **Camera** | | | | | |
| 1 | "Làm chậm mọi zoom xuống 0,7×" | *slow every zoom to 0.7x* | Camera bớt giật, chữ đọc kịp | thời lượng zoom ×(1/0,7)≈×1,43; giữ ease-out | [BÀI] (rexan) |
| 2 | "Đẩy vào nút bấm" | *push in on the button* | Mắt bị dẫn vào đúng thao tác | 1,3–1,5× trong 0,5–0,8 s `power3.out`, tâm = bbox trong capture-log | [GU] ≤1,5× |
| 3 | "Mở bằng cận (macro) rồi kéo lùi" | *open on macro, pull back* | Vào UI có "lộ diện", khỏi đập cả trang vào mặt | crop 2–2,5× (cần ảnh DPR 2) → 1× trong ~1 s `expo.out` | [ĐO] mercury 10,3–11,3 s |
| 4 | "Punch-in nhanh rồi thả" | *quick punch-in, then release* | Nhấn 1 vùng, chú thích gắn theo | 1,4–1,6× trong 0,5 s `power4.out`, giữ 2–2,5 s, về 1× 0,35 s `power3.in` (UI thật: ≤1,5×) | [ĐO] worker-previews |
| 5 | "Một camera liên tục, không cắt cứng" | *one continuous camera, no hard cuts* | Cảm giác one-take, cao cấp | push/pull/pan 1,5–3 s, ease-in-out mềm | [BÀI] (jake11moran) |
| 6 | "Giữ khung nhưng cho trôi nhẹ" | *hold with slow drift* | Khung đứng yên không chết | scale 1,00→1,03 suốt lúc giữ | [GU] |
| 7 | "Lùi ra sơ đồ rồi lặn vào nhánh" | *pull out to the map, dive into the branch* | Chuyển từ tổng quan xuống chi tiết bằng camera | lặn scale 1→3 trong 0,7 s `expo.inOut`; nhánh nở 3 thẻ nghiêng ±6° lệch 0,08 s | [ĐO] paid-media |
| **Cắt / chuyển cảnh** | | | | | |
| 8 | "Cắt cứng ở đây" | *hard cut here* | Nhấn mạnh 1 nhịp | tổng ≤ 6 cú/phim, chỉ nơi kế hoạch cho phép | [GU] PLAN v3.2 |
| 9 | "Cho phần tử đi xuyên qua cú cắt" | *carry the chip across the cut* | Hai cảnh dính nhau như one-take | phần tử ở layer riêng, giữ hình, 0,5 s `power3.inOut` tới đúng bbox nút | [ĐO] mercury 8,67 s |
| 10 | "Morph thẻ, đừng cắt" | *morph the card, don't cut* | Nội dung đổi mà container liên tục | `to(card,{width,height,x,y,radius},0.6,power3.inOut)`; nội dung cũ mờ trước 0,2 s, mới vào sau 0,25 s | [ĐO] paid-media |
| 11 | "Mở vòng tròn từ nút vừa bấm" | *circle wipe from the clicked button* | Bấm → cảnh sau bung ra từ chính nút | clip-path circle từ tâm bbox nút, 0,5–0,7 s | [BÀI] (M3 §2, move M3) |
| 12 | "Cắt tăng tốc, giữ nguyên một đường cong" | *accelerating cuts on one shared curve* | Hook 3 s đầu dồn dập nhưng liền mạch | 1,0→0,8→0,6→0,4→0,3 s/shot, đặt trên beat | [ĐO] opus-5-5 launch |
| 13 | "Quét khối màu che rồi mở" | *colour-block wipe* | Chuyển chương kiểu poster | hình chữ nhật lệch góc phủ khung 0,3–0,5 s rồi trượt đi; ≤1 màu accent nền | [NHÌN] ảnh tĩnh ref |
| 14 | "Bỏ flash/iris, dùng settle 1,06→1" | *drop flash and iris, settle in* | Mượt nằm trong khung | scale 1,06→1, 0,35 s `expo.out` | [GU] |
| **Chữ** | | | | | |
| 15 | "Chữ vào từng từ, xám rồi đậm" | *words in one by one, grey to ink* | Đọc theo nhịp, không nảy | stagger 0,12 s, 0,3 s/từ; cả câu drift 1,0→1,08 | [ĐO] launchvideo |
| 16 | "Chỉ đổi từ cuối của câu lặp" | *swap only the last word* | Nhịp điệu điệp cấu trúc | 1 s/từ, cũ y −10 mờ 0,2 s, mới từ y +10 0,25 s | [ĐO] mercury 29–31 s |
| 17 | "Chữ nhỏ hơn, khung trống hơn" | *smaller type, more air* | Sang, bớt ồn | ≥50% khung trống ở cảnh motion; 1 ý/khung | [ĐO] M1 KL2 |
| 18 | "Chữ nhấn từ khoá bằng màu accent" | *colour only the keyword* | Mắt bắt đúng từ mang nghĩa | tiêu đề 2 dòng, từ khoá màu accent; 1 accent/phim | [NHÌN] ảnh tĩnh ref |
| 19 | "Phụ đề nhấn đúng từ đang đọc" | *active-word subtitle* | Live caption khớp giọng | cụm 2–4 từ theo nghĩa, không tách từ ghép (định mức…) | [GU] |
| 20 | "Số chương cố định ở góc" | *pin a chapter counter* | Người xem biết đang ở đâu | `03 / 18` hoặc `01 TÊN CHƯƠNG`, không nhảy vị trí giữa cảnh | [NHÌN] ảnh tĩnh ref |
| **Nhịp** | | | | | |
| 21 | "Cho rơi đúng phách" | *land it on the beat* | Cắt/di chuyển khớp nhạc | mốc = `beats.json`; sai số đã đạt ≤ ~22 ms | [ĐO] NEXT (grid 41/41) |
| 22 | "Chờ một nhịp thở trước CTA" | *give it a breath before the CTA* | Cảnh cuối đủ tĩnh để đọc | 1,5–2 s ít chuyển động; khung cuối giữ hình | [BÀI] (Taxtello prompt) |
| 23 | "Mỗi 2–4 s phải có điều mới" | *something new every 2–4 s* | Không có khoảng chết | dùng cùng shot ≤2,5 s của taste; đếm bằng `check_shots.py` | [GU]/[BÀI] |
| 24 | "Đừng dừng cùng lúc, chồng lên nhau" | *overlap, don't stop together* | Chuyển động tự nhiên | mỗi phần tử lệch 60–120 ms | [BÀI]+[ĐX] |
| **Số / UI** | | | | | |
| 25 | "Số lăn kiểu odometer" | *odometer the number* | Số có trọng lượng | mỗi chữ số 1 cột, 0,8 s `power2.inOut`, cột phải chạy trước 0,03 s | [ĐO] mercury |
| 26 | "Về 0 rồi bật huy hiệu" | *count to zero, pop the badge* | Kết quả "xong" rõ | về 0 → badge `back.out(2)` 0,35 s | [ĐO] mercury 20–22 s |
| 27 | "Thanh co lại, chừa bóng gạch chéo" | *bar shrinks, hatched ghost stays* | Thấy phần bị "ăn" | lớp gạch chéo full cao + lớp đặc `scaleY` 1 s; nhãn −% vào sau | [ĐO] amplitude |
| 28 | "Con trỏ to hơn, chậm hơn" | *bigger, slower cursor* | Người xem theo kịp thao tác | ~56 px, x/y ease khác nhau, đứng ≥0,3 s trước khi bấm | [GU]+[BÀI] |
| 29 | "Lò xo nhẹ, không nảy" | *soft spring, no bounce* | Có khối lượng nhưng vẫn sang | overshoot ≤2% ở UI, 0% ở chữ | [BÀI] (article + Taxtello) |
| **Ánh sáng / chất liệu** | | | | | |
| 30 | "Sáng ấm sau vật thể, giữ UI sắc nét" | *warm bloom behind, keep the UI crisp* | Chiều sâu, không mờ sản phẩm | bloom sau object; vignette nhẹ; grain chỉ khi giúp ích; KHÔNG blur UI | [ĐO] mercury 6,5–8,5 s + [BÀI] |

**Thay câu mơ hồ:** "làm nó mượt hơn" → #14 hoặc #29 + địa chỉ · "sang hơn" → #17 + #30 · "nhanh hơn" → #23/#12 kèm số shot · "nổi bật hơn" → #18/#4 · "trông AI quá" → #17 + bỏ nhãn góc/HUD trang trí (#20 chỉ khi số thật).

## Cách agent sửa theo ghi chú

1. Đọc địa chỉ (`shot Rxx t=…` / `ô nhịp n`) → mở đúng shot trong `timeline.json` / capture-script; **không** đụng shot khác.
2. Áp ĐÚNG câu + con số. Thiếu con số ⇒ lấy thông số gợi ý ở bảng và **ghi lại số đã dùng** vào `decisions.md`.
3. Chỉ render lại đoạn đó ở 720p (pipeline/08-build.md), xem lại 1 dải 12 khung quanh chỗ sửa; full 1080p đúng 1 lần cuối.
4. Ghi chú không có địa chỉ / không có câu trong bảng (vd "mượt hơn", "sang hơn") → hỏi lại 1 câu, không đoán và không đổi lung tung.
5. Gu đã chốt (`references/taste-and-banlist.md`: zoom ≤ 1,5×, caption 92 px…) thắng bảng này khi hai bên mâu thuẫn.
