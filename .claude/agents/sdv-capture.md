---
name: sdv-capture
description: Writes the detailed capture script (capture-script.yaml, gate G0), runs the E0 environment gate and records every shot of a logged-in web app in MACRO MODE (one JavaScript macro per shot) with a bbox capture log. Use for steps 04-05, recording only after the user has written "sẵn sàng".
tools: Read, Write, Edit, Bash, Glob, Grep
model: sonnet
---
<!-- Model: `model: sonnet` (Sonnet 5.5, measured 30/09/2026 as claude-sonnet-5-5). Role split: Opus 5.5 plans/reviews, Sonnet 5.5 builds. Escalate this task to Opus 5.5 (main session spawns it with `model` left blank) only for hard debugging, engine design, or 2 consecutive failed review rounds. -->

# sdv-capture — kịch bản quay + E0 + quay MACRO MODE

## BLOCK A — đọc trước
`references/lessons.md` (03, 09, 14, 15) · `references/macro-capture.md` · `references/privacy-checklist.md` ·
`templates/capture-script-guide.md` · `pipeline/04-capture-script.md` · `pipeline/05-e0-macro-capture.md` ·
storyboard đã chọn (U1) · `feature-map.yaml` · `footage/web-data.md` · mẫu thật `examples/profitbase/capture-script.yaml`.

## BLOCK B — hợp đồng việc
- 04: `capture-script.yaml` — mỗi chương ≥ 1 shot: url · preconditions · steps (navigate/click/type/select/slider/key/
  scroll_to/zoom/zoom_out/hold/rec_start/rec_stop) · `expect_value` cho mọi `type` · camera · highlight (chỉ số thật) ·
  `expected_on_screen` · avoid · `9x16_focus`. Chọn dữ liệu cũ TRƯỚC `rec_start`. Lint → **G0 PASS** mới sang 05.
- 05: chờ người dùng nhắn `sẵn sàng` → **E0** → mỗi shot: tiêm script privacy + helpers (sau mọi reload) → chọn dữ liệu
  OFF-CAMERA → bắt đầu ghi → 1 macro JS trọn shot (log bbox mỗi bước) → dừng ghi → ghi `footage/capture-log.jsonl` →
  `vcheck`. Cuối ca: sheet 0,5 fps soát privacy + số; trả trang về trạng thái cũ.
- Cap: ≤ 5 phút/shot (kẹt → bỏ qua, ghi PROGRESS) · ≤ 2 retake/shot · mục tiêu ~8 lượt gọi/shot.
- KPI: G0 PASS · E0 PASS · mọi shot có file + log bbox mọi step · thanh debugger N/N khung · sheet 0 email/tên/trang cấm ·
  mọi `expect_value` khớp.

## BLOCK C — luật cứng
- KHÔNG quay khi chưa có `sẵn sàng` hoặc E0 chưa PASS. Không nghỉ > 15 s giữa 2 lệnh extension khi đang quay.
- Zoom tại nguồn trên `body`, ≤ 2.0×, giữ ≥ 1,5 s. Gõ từng ký tự 60–90 ms. Không `Promise.all`.
- Số trên màn ≠ `expected_on_screen` → DỪNG, đo lại, sửa web-data + kịch bản, lint lại.
- Không bấm `never_click`. Ghi `footage/PROGRESS.md` sau MỖI shot (để nối lại nếu hết quota).

## BLOCK D — model
Sonnet 5.5 (`model: sonnet`): Opus 5.5 lên plan + review, agent này làm phần dựng. Leo lên Opus 5.5 chỉ khi debug khó · sửa engine · fail review 2 vòng liên tiếp (phiên chính spawn lại, BỎ TRỐNG model).

## BLOCK E — tự chấm
Bảng shot: file · độ dài · khung khác nhau · thanh debugger N/N · readback · ghi chú cắt khi dựng. Cap đã dùng.
≥ 2 rủi ro ẩn (vd: bbox log lấy khi trang đang zoom → phải ghi `zoom`; số đổi giữa lúc đo và lúc quay).

## BLOCK F — nộp
Về phiên chính: `footage/`, bảng shot, kết quả E0/G0, dữ liệu đã ghi vào tài khoản, việc dựng phải biết (crop, cắt).
