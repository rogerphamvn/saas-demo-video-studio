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
| `lib/txfx-v2.js` | TX T1/T2/T5 + FX của gu v2 "kinetic slab" (bố cục nhiều scene) — ngoài ban-list v3, chỉ dùng khi khách chọn gu đó | không ai |
| `data/grid.js` | lưới BPM + chương (`scripts/music/conform_music.py` sinh) | script |
| `data/captions.js` | từ + cụm caption (`scripts/build/make_captions_js.py` sinh) | script |
| `data/cuts.js` | clip footage (`scripts/build/cut_clips.py` sinh) | script |
| `data/engine-cfg.js`, `data/motion-cfg.js` | cấu hình theo dự án (keepCrop, từ nhấn, chuyển chương, push) | integrator |
| `scenes/eXX.js` | 1 file/chương — builder song song | builder được giao |

Luật: tất định (không `Math.random`, `onUpdate`, ghi chữ lúc chạy, `filter: blur`, ease nảy); animate wrapper, không animate `<video>`;
thời điểm luôn từ `HF.bar()` / `HF.beat()` / `HF.W()`. Ban-list: `.claude/skills/saas-demo-video-studio/references/taste-and-banlist.md`.

ORIGIN: snapshot engine ca ProfitBase v3, chụp 28/09/2026 00:05 GIỮA motion pass v3.1.
**TODO(sync-v3.1):** thay `lib/engine.js` + `lib/motion-kit.js` bằng bản v3.1 cuối khi được duyệt.
