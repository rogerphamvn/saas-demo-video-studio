---
name: saas-demo-video-studio
description: >-
  Làm video REVIEW / giới thiệu / demo cho WEB APP · SaaS · website từ MÀN HÌNH THẬT (không mock) chỉ bằng 1 prompt:
  recon web chỉ-đọc → 3 storyboard cho người dùng chọn → kịch bản quay chi tiết (cổng G0) → cổng môi trường E0 + quay
  MACRO MODE trên Chrome đã đăng nhập → VO tiếng Việt (VieNeu local) căn từng từ → nhạc nắn theo lưới BPM → dựng HyperFrames
  + GSAP (tiêu đề chương, card UI thật, split-flap, chip cầu nối, 3D flip/push) bằng nhiều agent SONG SONG (Opus 5.5 lên plan/review, Sonnet 5.5 dựng) →
  mix −14 LUFS + SFX + .srt → 16:9 + 9:16 chia đôi → reviewer độc lập. Dùng khi người dùng nói: "làm video review cho <URL>",
  "video giới thiệu web app", "video demo SaaS", "quay màn hình giới thiệu chức năng", "video tour sản phẩm", "make a product
  demo video for my web app", "screen-recorded SaaS review video". KHÔNG dùng cho: video quay người thật/camera, motion
  graphic không có màn hình thật, video AI text-to-video.
metadata:
  version: "1.0.0"
  source_case: "examples/profitbase (26–28/09/2026)"
  models: "Opus 5.5 (phiên chính) = brief + plan + storyboard + review; Sonnet 5.5 (model: sonnet) = dựng/quay/mix; leo lên Opus 5.5 (spawn BỎ TRỐNG model) chỉ khi debug khó, sửa engine, hoặc fail review 2 vòng liên tiếp"
---

# SaaS demo video studio — video review web app từ 1 prompt

**Đọc trước (theo thứ tự, ~10 phút):** `references/lessons.md` → `references/taste-and-banlist.md` →
`references/qa-gates.md` → `references/privacy-checklist.md` → `references/macro-capture.md`.
Lệnh chạy từng bước: `pipeline/01…10-*.md` (gốc repo). Script: `scripts/` + `scripts/README.md`. Khung dựng: `engine/`.

> ROOT = thư mục chứa `pipeline/`, `scripts/`, `engine/` (gốc repo). Nếu chỉ copy `.claude/` sang dự án khác, clone repo
> cạnh đó và dùng đường dẫn tuyệt đối tới ROOT trong mọi lệnh.

## 1. Lời hứa và giới hạn (nói thẳng với người dùng ở tin nhắn đầu)

- 1 prompt `Làm video review cho <URL>` chạy hết pipeline; chỉ DỪNG ở 3 cổng người dùng (mục 3).
- Ra: `final-16x9.mp4` + `final-9x16.mp4` + `.srt` + `QA-REPORT.md` (số đo từng cổng).
- Cần: Windows (quay bằng ffmpeg gfxcapture/gdigrab), Chrome đã đăng nhập tài khoản demo + extension Claude in Chrome,
  Python 3.11+, ffmpeg, Node 18+, VieNeu-TTS local (hoặc key TTS khác). Tuỳ chọn: OPENAI_API_KEY (căn caption từng từ).
- Mới đo trên 1 ca (xem `references/cost-time.md`). "30–45 phút tới bản nháp" là MỤC TIÊU, chưa đo — bấm giờ và báo lại.

## 2. Mô hình điều phối (bắt buộc)

```
Phiên chính = ĐẠO DIỄN: lên PLAN (mục tiêu · lộ trình · phân công · SOP · KPI · cách nộp) → xin duyệt → giao việc → nghiệm thu
  │
  ├─ agent con chạy SONG SONG khi không phụ thuộc nhau. sdv-capture · sdv-voiceover · sdv-builder · sdv-audio-mix có `model: sonnet` (Sonnet 5.5);
  │     sdv-recon · sdv-reviewer để trống ⇒ kế thừa Opus 5.5 của phiên chính
  │     sdv-recon · sdv-capture · sdv-voiceover · sdv-builder (×1–3, chia theo chương) · sdv-audio-mix
  └─ sdv-reviewer (độc lập, chỉ đo + phản biện, không sửa) → phiên chính quyết: giao / trả việc kèm chỉ dẫn file:dòng
```

| Agent (`.claude/agents/`) | Bước | Chạy song song với |
|---|---|---|
| `sdv-recon` — Ca 0: soát web chỉ-đọc, feature-map, web-data, seed dữ liệu demo (nếu được phép) | 02 | storyboard (03) |
| `sdv-capture` — kịch bản quay + G0, cổng E0, quay macro, capture log | 04–05 | voiceover (06), music grid (07) |
| `sdv-voiceover` — VieNeu từng câu, kiểm phát âm 2 ASR, đặt câu lên lưới, căn chữ | 06 | capture |
| `sdv-builder` — engine + scenes/eXX.js, stills, cảnh thử, cắt footage, 9:16 | 03 (storyboard/stills), 08 | builder khác (chia chương), audio |
| `sdv-audio-mix` — nắn nhạc theo lưới, SFX plan, duck, −14 LUFS, .srt | 07, 09 | builder |
| `sdv-reviewer` — đo lại G0–G11, ≥ 3 phản biện, gap | 10 (+ sau U2) | builder sửa phần khác |

Luật giao việc: mỗi agent đọc file của mình trong `.claude/agents/` (khung 6 khối cố định) + đúng `pipeline/NN-*.md`;
**1 người ghi 1 file** (scene builder chỉ ghi `scenes/eXX.js` của mình; chỉ integrator ghi `index.html`); mỗi agent TỰ CHẤM
trước khi nộp (KPI đạt/không + bằng chứng, ≥ 2 rủi ro "hỏng mà không ai biết"). Phiên chính KHÔNG bê nguyên báo cáo agent
cho người dùng — tự kiểm lại trên bằng chứng (sheet, log, số đo) rồi mới trình.
Lệnh `hyperframes render` chạy ở PHIÊN CHÍNH (agent con có thể bị bộ lọc an toàn chặn lệnh nặng).

## 2b. Phân vai model (user chốt 30/09/2026)

> "sonnet 5.5 đang làm rất tốt, đảm bảo Opus 5.5 lên plan sau đó đưa cho sonnet 5.5 làm các video motion nhé, phần nào khó quá thì mới cho opus 5.5 làm"

| Việc | Model | Cách spawn |
|---|---|---|
| brief · plan · storyboard · review cuối | Opus 5.5 (phiên chính) | — |
| dựng scene, quay theo kịch bản, mix âm, chuẩn bị render | Sonnet 5.5 | `model: sonnet` trong `.claude/agents/*.md` |
| debug khó · thiết kế/sửa engine · builder fail review 2 vòng liên tiếp | Opus 5.5 | spawn lại, **BỎ TRỐNG** `model` |

Phân vai này mới áp từ 30/09/2026, **chưa có số đo** (bao nhiêu vòng review / video); ghi lại ở ca đầu.

## 3. Ba cổng người dùng (và cách bỏ qua bằng mặc định)

| Cổng | Khi nào | Người dùng làm | Bỏ qua bằng mặc định |
|---|---|---|---|
| **U1 — chọn storyboard** | sau bước 03 | chọn A/B/C (+ trả lời ≤ 6 câu hỏi quyết định) | prompt có `storyboard: B` hoặc `auto` → lấy bản đề xuất |
| **U0 — "sẵn sàng"** | trước bước 05 (quay) | để máy YÊN, đóng app AI khác, nhắn đúng chữ `sẵn sàng` | KHÔNG bỏ được — quay khi người dùng đang dùng máy sẽ hỏng (LESSON-15). Chỉ gộp được: nhắn `sẵn sàng` ngay trong prompt nếu máy đã để yên từ đầu |
| **U2 — duyệt stills + cảnh thử** | sau khi dựng 1 khung tĩnh/chương + cảnh thử 15–20 s | góp ý kiểu đạo diễn ("E4 ô 12: zoom chậm lại") | prompt có `duyệt U2: auto` → dựng hết, người dùng chỉ xem bản nháp |

## 4. Pipeline 10 bước (chi tiết + lệnh: `pipeline/`)

| # | Bước | Ra | Cổng |
|---|---|---|---|
| 01 | Brief từ prompt (URL, loại A–E, độ dài, giọng, màu, trang cấm, CTA) | `brief.md` | hỏi 1 lượt, gom mọi câu hỏi |
| 02 | Recon chỉ-đọc + web-data + seed demo | `feature-map.yaml`, `footage/web-data.md` | số chỉ lấy từ web |
| 03 | 3 storyboard trên lưới BPM | `storyboard/SB-A,B,C.md` | **U1** |
| 04 | Kịch bản quay chi tiết | `capture-script.yaml` | **G0 PASS** |
| 05 | E0 + quay macro | `footage/*.mkv`, `markers.txt`, `capture-log.jsonl` | **U0**, **E0**, vcheck/shot, sheet privacy cuối ca |
| 06 | VO từng câu + phát âm + lưới + căn chữ | `vo/voiceover.wav`, `placements.json`, `captions.json` | G1, G1b |
| 07 | Nhạc nắn theo lưới | `assets/audio/music-grid.wav`, `data/grid.json` | G2 |
| 08 | Dựng: cuts → erase pointer → scenes → stills → cảnh thử | `index.html` + `scenes/` | **U2**, G3–G5b, G9 |
| 09 | SFX plan + mix + master + .srt | `assets/audio/mix.m4a`, `.srt` | G6 |
| 10 | Render 16:9 + 9:16 (thư mục riêng) + QA + giao | `deliver/` | G7, G8, G9, G11, G10 reviewer |

Song song hoá: 02 ∥ 03 · 05 ∥ 06 ∥ 07 · 08 chia 1–3 builder theo nhóm chương · 10: render 16:9 và 9:16 cùng lúc nếu máy chịu nổi.

## 5. Luật không được phá (mỗi dòng = 1 lỗi đã trả giá)

1. **Số trên hình = số trong `web-data`** (đo trên web lúc quay). Không số giả, không % tự tính.
2. **Không quay khi chưa có `capture-script.yaml` qua G0**; giá trị demo sẽ gõ chốt sẵn trong kịch bản.
3. **Không quay khi E0 chưa PASS** và người dùng chưa nhắn `sẵn sàng`.
4. **Mỗi shot 1 macro JS**, `expect_value` trong macro; chọn dữ liệu cũ OFF-CAMERA; kẹt > 5 phút thì bỏ qua shot.
5. **Chọn BPM trước, mọi thứ bám lưới**: drop/cắt/cử chỉ số rơi đầu ô; nhạc nắn theo lưới, không ngược lại.
6. **Privacy tại nguồn** + sheet cuối ca; không bấm `never_click`; trả trang về trạng thái cũ sau ca.
7. **1 người ghi 1 file**; biến thể (9:16) = thư mục dự án riêng, không sửa tạm file chung.
8. **Engine tất định**: không `Math.random`, `onUpdate`, ghi chữ lúc chạy, `filter: blur`, ease nảy; animate wrapper, không `<video>`.
9. **Vòng sửa**: render đoạn 720p; full 1080p 1 lần/bản; reviewer song song; phiên chính xem sheet 1 fps sau MỖI render.
10. **Không tin cổng xanh khi nó so dữ liệu với chính nó** — hỏi "script đọc cái gì?".

## 6. Cấu trúc thư mục 1 dự án video

```
<project>/
  brief.md  feature-map.yaml  capture-script.yaml  project.json
  footage/  web-data.md  <shot>_t1.mkv  markers.txt  capture-log.jsonl   (không commit)
  vo/       script.txt  raw/  lines/  voiceover.wav  placements.json  captions.json
  storyboard/ SB-A.md SB-B.md SB-C.md  stills/
  comp/     (copy của engine/ = paths.comp_dir)  index.html  tokens.css  lib/  scenes/  data/  assets/{fonts,audio,footage}
  comp-9x16/ (sinh bởi build_916.py — KHÔNG sửa tay)
  deliver/  final-16x9.mp4  final-9x16.mp4  <name>.srt  QA-REPORT.md
```

## 7. File trong skill

| File | Vai trò |
|---|---|
| `references/lessons.md` | 15 bài học + gotcha kỹ thuật |
| `references/taste-and-banlist.md` | gu mặc định, 15 move, ban-list, lịch sử chê → sửa |
| `references/qa-gates.md` | G0–G11 + E0: đạt khi nào, đọc gì, lỗi thật đã gặp |
| `references/macro-capture.md` | cổng E0 + cách viết macro 1 lệnh/shot + privacy tại nguồn |
| `references/privacy-checklist.md` | checklist che thông tin |
| `references/capture-script-by-app-type.md` | recon → feature-map → nháp kịch bản cho 8 dạng app |
| `references/director-notes.md` | từ điển 30 câu ghi chú đạo diễn (địa chỉ + câu + con số) dùng khi sửa ở U2 / sau review |
| `references/cost-time.md` | chi phí / token / thời gian đo thật + bảng bấm giờ cho ca sau |
| `templates/prompt-launch-video.md` | mẫu prompt "video ra mắt sản phẩm" trọn quy trình có 3 cổng (EN + VI), chưa chạy ca thật |
| `templates/` | brief, feature-map, storyboard, kịch bản quay (YAML + hướng dẫn), kịch bản VO 30/45/70 s |
