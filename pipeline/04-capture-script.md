# 04 · Kịch bản quay chi tiết (agent `sdv-capture`) → cổng G0

**Input:** storyboard đã chọn, `capture-script.draft.yaml`, `footage/web-data.md`, `project.json` (mục privacy).

**Làm:** mỗi chương ≥ 1 shot: `url · preconditions · steps · expect_value · camera · highlight · expected_on_screen · avoid · 9x16_focus`
(hướng dẫn `templates/capture-script-guide.md`; mẫu thật `examples/profitbase/capture-script.yaml`). Bước chọn dữ liệu cũ đặt
TRƯỚC `rec_start` (OFF-CAMERA). Giá trị demo gõ chốt sẵn. Đủ `forbidden_pages`, `global_avoid`, `never_click`.

```bash
python scripts/capture/capture_log_to_edit.py lint --script capture-script.yaml --web-data footage/web-data.md
python scripts/capture/clean_js.py --config project.json --with-helpers     # JS làm sạch privacy + helpers, sinh từ project.json
```

**Output:** `capture-script.yaml`, `footage/sdv-clean.js`.

**Cổng G0:** in `G0 PASS` — mọi số phải thấy có trong web-data, không trang cấm, không bấm `never_click`, zoom trong giới hạn.
