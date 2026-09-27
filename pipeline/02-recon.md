# 02 · Recon chỉ-đọc + web-data + seed demo (agent `sdv-recon`, song song với 03)

**Input:** `brief.md`; Chrome đã đăng nhập; extension Claude in Chrome.

**Làm:** mở từng route (tab riêng) → `feature-map.yaml` (template `templates/feature-map-template.yaml`; 8 dạng app:
`references/capture-script-by-app-type.md`) · ghi mọi con số có thể lên hình vào `footage/web-data.md` (nguyên văn + route + giờ) ·
đo dpr, viewport sau F11, `crop_top` · seed bản ghi `Demo · …` chỉ khi brief cho phép. Nháp kịch bản cho bước 04:

```bash
python scripts/capture/capture_log_to_edit.py draft --feature-map feature-map.yaml --out capture-script.draft.yaml
```

**Output:** `feature-map.yaml`, `footage/web-data.md`, danh sách dữ liệu demo đã tạo.

**Cổng:** 0 nút ghi DB ngoài seed được duyệt · mọi `wow_element.number` có trong web-data · trang trống → `data_ok: false`.
