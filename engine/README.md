# engine/ — khung dựng HyperFrames + GSAP

Copy cả thư mục này thành `<project>/comp/` (= `paths.comp_dir`). Chạy được ngay với dữ liệu mẫu (khung footage là ô xám "FOOTAGE SLOT"):

```bash
# 1. font (OFL, không kèm trong repo) -> assets/fonts/
curl -L -o assets/fonts/Inter-var.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz,wght%5D.ttf"
curl -L -o assets/fonts/IBMPlexSerif-Italic.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/ibmplexserif/IBMPlexSerif-Italic.ttf"
curl -L -o assets/fonts/IBMPlexSerif-BoldItalic.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/ibmplexserif/IBMPlexSerif-BoldItalic.ttf"
# 2. kiểm
npx --yes hyperframes@0.8.78 lint     # dữ liệu mẫu: 1 lỗi duy nhất = thiếu assets/audio/mix.m4a (sinh ở bước 09) - đúng
```

Đã kiểm 28/09/2026: 3 URL font tải được; `lint` ra đúng 1 lỗi trên (thiếu mix); mở `index.html` headless + seek t = 4 s
→ timeline dựng xong, không lỗi trang (ảnh chụp: tiêu đề "01 / 02", callout split-flap, caption).

| File | Vai trò | Ai ghi |
|---|---|---|
| `index.html` | composition 1920×1080: lớp nền · tiêu đề · card UI · callout · số khổng lồ · fx · chip · caption; FOOTAGE markers | integrator |
| `tokens.css` | màu (1 accent), layout, font | integrator |
| `lib/engine.js` | hợp đồng `window.HF`: `bar/beat/W` (thời điểm) · `card/title/slot/target` · `callout/pill/wait` · `odoHTML/odo` (split-flap) · `giant/strip/light` · `punch/macro/push` · `curve/chipTo/chipShow/chipHide/circleWipe` · `captions` | không ai (chỉ đồng bộ bản mới) |
| `lib/motion-kit.js` | lớp motion chung: card tilt 3D, chuyển chương flip/push/zoom/slab/drop + sweep, push-in theo bbox, bloom+burst ở drop | không ai |
| `lib/v6-kit.js` + `lib/v6.css` | **v6 upgrade layer (generic, optional)**: 4 chuyển cảnh 3D rơi ĐÚNG PHÁCH (`flip` · `push` · `zoom` · `drop`), split-flap lật thẳng từ ô trống sang chữ số CUỐI (không bao giờ hiện số trung gian sai), tilt drift + parallax, Z-lift, sweep, bloom + burst, lower-third; API `window.V6_KIT(ctx)` (hợp đồng `ctx` ở đầu file). Chạy trên layout **nhiều scene** (`#stage > .scene`), khác layout chapter-tour của `engine.js` | không ai |
| `lib/txfx-v2.js` | TX T1/T2/T5 + FX của gu v2 "kinetic slab" (bố cục nhiều scene) — ngoài ban-list v3, chỉ dùng khi khách chọn gu đó | không ai |
| `data/grid.js` | lưới BPM + chương (`scripts/music/conform_music.py` sinh) | script |
| `data/captions.js` | từ + cụm caption (`scripts/build/make_captions_js.py` sinh) | script |
| `data/cuts.js` | clip footage (`scripts/build/cut_clips.py` sinh) | script |
| `data/engine-cfg.js`, `data/motion-cfg.js` | cấu hình theo dự án (keepCrop, từ nhấn, chuyển chương, push) | integrator |
| `scenes/eXX.js` | 1 file/chương — builder song song | builder được giao |

Luật: tất định (không `Math.random`, `onUpdate`, ghi chữ lúc chạy, `filter: blur`, ease nảy); animate wrapper, không animate `<video>`;
thời điểm luôn từ `HF.bar()` / `HF.beat()` / `HF.W()`. Ban-list: `.claude/skills/saas-demo-video-studio/references/taste-and-banlist.md`.

## Nguồn gốc (ORIGIN) — 2 lớp

1. `engine.js` + `motion-kit.js` + `txfx-v2.js` + `index.html`: **snapshot** engine ca ProfitBase v3 (28/09/2026 00:05, giữa motion pass v3.1). Pass v3.1 **không được hoàn tất**: bản v3 bị từ chối, phong cách đã duyệt vẫn là v5. Giữ lại như **layout chapter-tour thay thế**, không đồng bộ nữa (thay cho `TODO(sync-v3.1)` cũ).
2. `v6-kit.js` + `v6.css`: dòng nâng cấp **được duy trì** — v6 = bản v5 đã duyệt + lớp nâng cấp bật/tắt được (LESSON-16: bản đã duyệt thì giữ nguyên diện mạo, chỉ chồng nâng cấp lên). Tổng quát hoá từ `lib/v6.js`/`v6.css` của ca ProfitBase 30/09/2026: **bỏ hết chữ/số của sản phẩm và đường dẫn**; các khối riêng của ca (hook, dots+gauge, trước/sau, KPI strip, bento) KHÔNG kèm — tự dựng bằng helper của kit.

## Trạng thái kiểm chứng (nói thẳng)

| Phần | Trạng thái | Bằng chứng |
|---|---|---|
| Bản v6 gốc của ca ProfitBase (16:9) | **ĐÃ RENDER trong ca thật** (30/09/2026); 12 chuyển cảnh Δ ≤ 12 ms so với lưới nhịp, 155 lần gọi FX/TX, 0 lỗi trang, lint 0 lỗi; 9:16 chưa làm | số đo của ca (không kèm trong repo) |
| `lib/v6-kit.js` + `lib/v6.css` bản TỔNG QUÁT (file này) | **SMOKE-TESTED** (mức cao nhất được nhận): `node --check` OK; nạp trong Chrome headless với GSAP 3.14 và trang tổng hợp 3 scene: `V6_KIT` dựng được, 2 chuyển cảnh (flip, zoom) rơi đúng phách (dBeat 0), split-flap lật quan sát khung giữa chừng chỉ thấy ô trống hoặc chữ số cuối, `hero`/`lowerThird`/`svgFlap` chạy không lỗi. **CHƯA render một video đầy đủ, CHƯA qua `hyperframes lint`/render, CHƯA thử trên layout ngoài ca** | smoke tự viết, 30/09/2026 |
| `engine.js`, `motion-kit.js`, `txfx-v2.js` | snapshot v3; đã kiểm 28/09 (lint + seek 4 s), KHÔNG đồng bộ thêm | mục "Đã kiểm" ở trên |
| Cách nối kit vào `engine.js` (ctx: `tl=HF.tl`, `beat0=HF.G.t0`…) | **UNTESTED** — chỉ mô tả trong header `v6-kit.js` | — |

Cảnh báo CSS: `v6.css` đặt class toàn cục `.frame`, `.w`, `.wi` (bản gốc dùng vậy); nếu trang của bạn đã có class trùng tên thì đổi trước khi nạp.

