# 05 · Cổng E0 + quay MACRO MODE (agent `sdv-capture`) → cổng U0

**Input:** `capture-script.yaml` (G0 PASS), `footage/sdv-clean.js`, Chrome mở với 4 cờ chống giảm vẽ + `--start-fullscreen`.
Lý do từng bước: `references/macro-capture.md`.

**U0:** agent nhắn người dùng: đóng app AI khác, để máy yên, trả lời `sẵn sàng`. Không quay trước khi có chữ đó.

```bash
powershell -ExecutionPolicy Bypass -File scripts/capture/keepawake.ps1       # giữ màn hình sáng (chạy nền)
python scripts/capture/e0_gate.py --config project.json --motion 10          # app AI khác · cờ Chrome · motion gate
# javascript_tool: tiêm footage/sdv-clean.js; kiểm document.visibilityState === "visible"
# --- mỗi shot ---
python scripts/capture/rec.py R01-boms_t1 --config project.json              # chạy nền; dừng khi có file footage/STOP_R01-boms_t1
#   1 lệnh javascript_tool = macro trọn shot (mẫu: references/macro-capture.md §2), bbox từng bước vào window.__log
#   tạo file STOP_<name>; ghi window.__log ra footage/capture-log.jsonl
#   (log dạng rút gọn "step|action|t|bbox|value|selector": python scripts/capture/ingest.py <shot> <take> --config project.json)
python scripts/capture/vcheck.py footage/R01-boms_t1.mkv --config project.json   # độ dài · khung khác nhau · thanh debugger N/N
# --- cuối ca ---
python scripts/capture/vcheck.py footage/<shot>.mkv --sheet --config project.json # sheet soát privacy + số (mắt người)
```

**Output:** `footage/<shot>_t<n>.mkv`, `footage/markers.txt`, `footage/capture-log.jsonl`, `footage/PROGRESS.md`.

**Cổng:** E0 PASS (≥ 25 khung đổi/s; 10–25 → HOLD mode; < 10 → dừng) · mỗi shot: thanh debugger N/N, `expect_value` khớp ·
cuối ca: sheet 0 email / 0 tên tài khoản / 0 trang cấm. Shot kẹt > 5 phút → bỏ qua, ghi PROGRESS.
