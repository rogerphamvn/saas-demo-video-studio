# 03 · Ba storyboard trên lưới BPM (agent `sdv-builder`) → cổng U1

**Input:** brief, feature-map (+ ảnh recon làm chỗ giữ), VO nháp 1 câu/chương (`templates/vo-script-templates.md`).

**Làm:** chọn BPM TRƯỚC (vd 124 BPM → ô 1,935 s), số ô ≈ độ dài mục tiêu, 3 drop. Viết `storyboard/SB-A.md`, `SB-B.md`, `SB-C.md`
theo `templates/storyboard-template.md` — khác nhau ở bố cục + nhịp, cùng số liệu và thứ tự chương. Mỗi chương: 1 thao tác chính,
tiêu đề 2 dòng, 1 cử chỉ số [WD], move m1–m15, SFX, shot nguồn. Tự đo trên giấy: cắt cứng ≤ 6, UI thật 60–75%, lặng ≤ 2,5 s.
Mẫu thật: `examples/profitbase/storyboard-B.md`. Kèm ≤ 6 câu hỏi quyết định, mỗi câu có mặc định.

**Output:** 3 storyboard + `vo/script.txt` (định dạng `E1|câu…`, 1 dòng = 1 chương).

**Cổng U1:** người dùng chọn A/B/C (hoặc `storyboard: auto` → bản đề xuất). Không dựng gì trước U1.
