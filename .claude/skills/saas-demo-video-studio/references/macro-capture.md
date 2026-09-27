# Quay MACRO MODE + cổng môi trường E0

> Mặc định từ 27/09/2026. Khách đánh giá sau ca mẫu: "cách tăng tốc này hiệu quả hơn cách cũ, nhanh hơn mượt hơn".
> Lệnh chạy cụ thể: `pipeline/05-e0-macro-capture.md`. File này giải thích VÌ SAO và CÁCH viết macro.

## 1. Cổng E0 — chạy TRƯỚC shot đầu, kiểm bằng LỆNH (không tin lời "đã tắt")

Mỗi dòng là 1 lần hỏng thật trong ca mẫu (65 phút đầu chỉ ra ~70% một shot):

| # | Kiểm | Vì sao | Cách kiểm |
|---|---|---|---|
| 1 | Không có agent/AI khác gắn vào Chrome hay chiếm CPU | 1 agent khác cùng gắn debugger → thanh debugger đổi tên qua lại, Chrome chỉ trình ~1 khung/s | `tasklist` không có app AI khác (danh sách cấu hình được); đóng cả biểu tượng khay hệ thống |
| 2 | Chrome chạy với 4 cờ chống giảm vẽ khi bị che | cửa sổ khác che Chrome → Chrome giảm vẽ còn 1–5 khung/s | command line tiến trình Chrome có `--disable-backgrounding-occluded-windows --disable-renderer-backgrounding --disable-background-timer-throttling --disable-features=CalculateNativeWinOcclusion`. Chrome "chạy nền khi đóng" sẽ BỎ QUA cờ mới → thoát hẳn (`taskkill`) rồi mở lại; mở kèm `--start-fullscreen` khỏi bấm F11 |
| 3 | Tab mà extension điều khiển là tab ĐANG HIỆN | relaunch xong extension tạo tab NỀN → `visibilityState: hidden`, quay ra khung đứng | JS: `document.visibilityState === 'visible'`; nếu không → người dùng bấm vào tab đó 1 lần và đóng tab thừa |
| 4 | Motion gate 10 s | đo thật số khung thay đổi/giây khi trang chuyển động | ≥ 25 khung đổi/s → quay thường · 10–25 → HOLD mode (giữ ≥ 2 s sau mỗi thay đổi) · < 10 → DỪNG, không đốt retake |
| 5 | Không nghỉ quá 15 s giữa 2 lệnh extension | thanh debugger tự tắt sau ~20 s không gọi → trang nhảy 70 px, `crop_top` sai; bắt cửa sổ theo HWND có thể đứng hình khi cửa sổ đổi cỡ | ping extension ngay trước `rec_start`; quay theo MÀN HÌNH (monitor 0) thay vì HWND |

Kèm: giữ màn hình sáng suốt ca (script keep-awake), `crop_top` đo 1 lần sau khi thanh debugger ổn định (ca mẫu: 70 px),
viewport 1920×1010 @ dpr 1 trong F11.

**Cổng người dùng U0 "sẵn sàng":** agent KHÔNG đưa Chrome lên trước / không quay khi người dùng chưa nhắn "sẵn sàng" —
người dùng phải để máy yên suốt ca quay (ca mẫu: ~14 phút Ca 1 + ~17 phút Ca 2+3).

## 2. MACRO MODE — mỗi shot MỘT lệnh JS

Cũ: 20–40 lượt gọi extension rời/shot (click, type, wait…) → giữa 2 thao tác có quãng chờ LLM → hình khựng, tốn token.
Mới: `rec_start` → **1 lệnh `javascript_tool` chạy trọn shot** → `rec_stop` → rút `window.__log` ra `capture-log.jsonl`.

| Đo trên cùng máy (laptop 4 nhân, không GPU rời) | Số shot | Thời gian | Thời gian/shot | Lượt gọi/shot |
|---|---|---|---|---|
| Từng bước (Ca 1) | 7 | ~14 phút (kể cả test + gate + reset dữ liệu) | ~2,0 phút | ~13,9 |
| Macro (Ca 2+3) | 10 | 17 phút | ~1,7 phút | ~7,6 |

Tiết kiệm lớn nhất là số lượt agent (≈ token). Số đo: 1 ca, 1 máy.

### Quy tắc viết macro
- click: `el.click()` + phát pointer/mouse events; gõ: native value setter của React + event `input` TỪNG ký tự, 60–90 ms/ký tự;
  cuộn: `scrollIntoView({behavior:'smooth'})` hoặc helper cuộn tất định; zoom: `transform: scale()` trên **body**
  (zoom trên `#root` không phóng dialog/portal); chờ: `setTimeout`.
- Mỗi bước có `expect_value` NGAY trong macro: đọc lại value/chữ, sai thì `throw` và trả về số bước hỏng.
- Chọn bản ghi trong combobox liệt kê dữ liệu cũ → macro RIÊNG, NGOÀI hình, trước `rec_start`.
- Bước cần hover thật (tooltip) thì bỏ: sự kiện tổng hợp không kéo chuột thật; con trỏ ảo khi dựng lấy từ bbox trong log.
- Không bao giờ `Promise.all`/gọi song song trong trang; JS tuần tự.
- `rec_stop` gọi lệnh riêng thì trễ 4–5 s sau cú click cuối → khi dựng cắt tại click + 1 s.
- Kiểm dồn cuối ca: sau mỗi shot chỉ `vcheck` nhanh (độ dài, số khung khác nhau, thanh debugger N/N); sheet 0,5 fps soi privacy/số làm MỘT lần cuối ca.
- Shot kẹt > 5 phút → bỏ qua, ghi PROGRESS, làm shot sau.

### Khung macro (MẪU viết lại từ mô tả ca mẫu — chưa chạy nguyên văn; tiêm `sdv-capture-helpers.js` trước)

```js
(async () => {
  const log = (window.__log = window.__log || []);
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const push = (line) => log.push(JSON.parse(line));            // __sdvLog/__sdvZoom trả 1 dòng JSON (bbox + epoch)
  const typeInto = async (el, text, ms = 75) => {                // native setter + input từng ký tự (React)
    const proto = el.tagName === "TEXTAREA" ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    const set = Object.getOwnPropertyDescriptor(proto, "value").set;
    el.focus(); set.call(el, ""); el.dispatchEvent(new Event("input", { bubbles: true }));
    for (const ch of text) { set.call(el, el.value + ch); el.dispatchEvent(new Event("input", { bubbles: true })); await sleep(ms); }
    el.dispatchEvent(new Event("change", { bubbles: true }));
  };
  const SHOT = "S02-editor";
  try {
    push(__sdvLog(SHOT, 1, "click", "text=Giá bán"));             // step 1: log bbox TRƯỚC khi thao tác
    const price = __sdvField("Giá bán"); price.click(); await sleep(400);
    push(__sdvLog(SHOT, 2, "type", "text=Giá bán"));
    await typeInto(price, "899000");
    if (price.value.replace(/\D/g, "") !== "899000") throw new Error("step 2 expect_value");
    await sleep(1200);                                            // giữ ≥ 1 s sau khi số dừng
    push(__sdvZoom(SHOT, 3, "text=Lợi nhuận ròng", 1.8, 700));    // zoom TẠI NGUỒN, giữ ≥ 1,5 s
    await sleep(1800);
    push(__sdvZoomOut(SHOT, 4, 700)); await sleep(900);
    return { ok: true, steps: log.filter((l) => l.shot === SHOT).length };
  } catch (e) {
    return { ok: false, error: String(e), last_step: log.length };
  }
})()
```

Sau shot: đọc `window.__log` ra file (`capture-log.jsonl`, 1 dòng JSON/step), rồi `window.__log = []`.

## 3. Privacy TẠI NGUỒN (trước khi quay, không che khi dựng)

Tiêm script làm sạch cấu hình được (`scripts/capture/js/`) sau MỖI lần reload cứng: ẩn email/badge vai trò/mục admin/nút chat nổi/
toaster, thay chữ theo NODE (React có thể tách "Chào buổi tối, <tên>!" thành 5 text node — CSS và regex trên cả chuỗi không bắt được),
ẩn dòng/bản ghi cũ không thuộc dữ liệu demo. Kiểm: `get_page_text` từng route không còn chuỗi cấm. Cuối ca: sheet 0,5 fps soát lại.
