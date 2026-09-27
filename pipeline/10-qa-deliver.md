# 10 · Render 16:9 + 9:16 + QA + reviewer + giao (phiên chính + `sdv-reviewer`)

**Input:** `<comp>/` đã qua U2 và bước 09.

```bash
python scripts/build/build_916.py --config project.json         # sinh <comp>-9x16/ (thư mục RIÊNG, không sửa tay)
# render ở PHIÊN CHÍNH (agent con có thể bị chặn lệnh nặng); nếu lỗi headless shell: set PRODUCER_HEADLESS_SHELL_PATH
cd <comp>       && npx --yes hyperframes@0.8.78 render -o ../deliver/final-16x9.mp4 --workers 3 --quality delivery
cd <comp>-9x16  && npx --yes hyperframes@0.8.78 render -o ../deliver/final-9x16.mp4 --workers 3 --quality delivery
python scripts/qa/check_loudness.py deliver/final-16x9.mp4 --w 1920 --h 1080 --fps 30
python scripts/qa/check_loudness.py deliver/final-9x16.mp4 --w 1080 --h 1920 --fps 30
python scripts/qa/check_layout_9x16.py <comp>-9x16/index.html
python scripts/qa/check_shots.py deliver/final-16x9.mp4 0.3
python scripts/qa/contact_sheet.py deliver/final-16x9.mp4 --step 1 --out deliver/qa
python scripts/qa/contact_sheet.py deliver/final-9x16.mp4 --step 1 --out deliver/qa
```

Rồi spawn `sdv-reviewer` (model bỏ trống) — tự chạy lại các cổng, ≥ 3 phản biện, ghi `deliver/QA-REPORT.md`.
Chưa đạt → chỉ dẫn file:dòng cho builder/audio → sửa → render ĐOẠN 720p → full 1 lần cuối. Tối đa 3 vòng.

**Output:** `deliver/final-16x9.mp4`, `deliver/final-9x16.mp4`, `deliver/<name>.srt`, `deliver/QA-REPORT.md`.

**Cổng:** G7 trên TỪNG file giao · G8 cắt cứng ≤ 6 · G9 sheet 1 fps cả 2 bản (privacy, chữ cụt, khung trống, 2 nhãn mâu thuẫn,
badge nháp tắt) · G11 |trống trên − trống dưới| ≤ 80 px · G10 reviewer ĐẠT. Sau giao: báo người dùng dữ liệu demo đã tạo trong tài khoản.
