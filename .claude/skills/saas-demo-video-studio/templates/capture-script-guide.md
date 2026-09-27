# Kịch bản quay chi tiết (capture script): hướng dẫn cho người không kỹ thuật

> Khách nói sau ca ProfitBase (26/09/2026): *"clip đầu vào phải chuẩn, ví dụ kịch bản chi tiết, kéo tới phần nào, vô phần
> nào, highlight phần nào, zoom in, zoom out cái nào… clip gốc chuẩn thì clip edit dễ hơn"*.
> Mẫu trống: `capture-script-template.yaml`. Mẫu điền đủ từ ca thật: `examples/profitbase/capture-script.yaml` (gốc repo).

## 1. Vì sao phải có

Ca ProfitBase lúc quay chỉ ghi giờ bắt đầu từng cảnh. Vì vậy khi dựng phải:
- dò con trỏ trên từng khung hình theo màu để dựng con trỏ ảo, rồi đoán vùng cần phóng to;
- cắt 1 cảnh thành 3 đoạn cho khớp lời đọc;
- bỏ các trang trống, che đoạn chat cũ có chữ "API key";
- cắt đoạn gõ nhầm số (909%) rồi gõ lại.

Cả ca tốn 5 vòng dựng, 7 lượt reviewer và 373 phút agent cộng dồn (~6,2 giờ) — xem references/cost-time.md.
Không phải toàn bộ số giờ đó do thiếu kịch bản: bản 9:16 làm lại 3 lần và việc chốt gu muộn cũng góp phần. Nhưng các lỗi
liệt kê ở trên đều lộ ra được ngay trên giấy, trước khi quay, nếu có kịch bản quay chi tiết.

## 2. Một SHOT gồm những gì (điền mỗi cảnh 1 khối)

| Trường | Nghĩa (nói thường) | Ví dụ |
|---|---|---|
| `id` | tên cảnh | `s03-payback` |
| `vo_line` | câu lời đọc phát trong lúc cảnh này hiện; `anchor_word` = từ mà khoảnh khắc chính phải rơi vào | "…hoà vốn ở đơn thứ chín…", neo "hoà vốn" |
| `duration_target` | cảnh dài bao nhiêu giây trên phim (bằng độ dài câu đọc) | `8.7` |
| `url` | trang nào | `/compare` |
| `preconditions` | phải sẵn sàng gì TRƯỚC khi quay: đã đăng nhập, có dữ liệu demo, zoom trình duyệt 100%, tắt widget, **trang KHÔNG trống** | "khung chat trống" |
| `steps` | từng thao tác theo thứ tự: `navigate` (mở trang) · `scroll_to` (kéo tới) · `hover` (rê chuột vào) · `click` (bấm) · `type` (gõ, kèm tốc độ gõ `type_delay_ms`) · `wait` (chờ) · `hold` (đứng yên). `hold_s` = giữ bao nhiêu giây | `{action: hover, selector: "text=Break-Even Point", hold_s: 3}` |
| `selector` | chỉ vào đâu trên trang: tên kỹ thuật (CSS) hoặc `text=<chữ đang hiện>` | `text=Tổng COGS / đơn` |
| `camera` | lúc nào phóng to vào đâu, mức bao nhiêu (**tối đa 1.5×**, hơn nữa chữ bị nhoè), lúc nào thu về (`zoom_out_at`) | `{t_rel: 3.0, zoom_to: "text=Thu Hồi Vốn", level: 1.5}` |
| `highlight` | làm nổi phần nào: `spotlight` (làm tối xung quanh) · `underline` (gạch chân) · `box` (khung) · `callout` (nhãn số). `text` = **chỉ số có thật trên web** | `{kind: callout, text: "13 units"}` |
| `cursor` | con trỏ đi qua những chỗ nào, theo thứ tự | `["text=Batch A", "text=Batch B"]` |
| `expected_on_screen` | các con số/chữ PHẢI thấy trên màn hình, và phải có trong file số liệu đã soát (web-data) | `["9 units", "13 units", "43%"]` |
| `avoid` | cái không được lên hình: email, vai trò admin, tên nhà cung cấp AI, menu quản trị, chat cũ, tab trống; trang cấm quay; **KHÔNG bấm Lưu** | `{selector: "text=API key", reason: "chat cũ"}` |
| `9x16_focus` | khi làm bản dọc (Reels/TikTok) thì giữ vùng nào | `text=Kết luận` |

Cảnh không quay (thẻ chữ, logo, montage trên ảnh chụp) thì ghi `capture: false` và `replace_with: "<dùng gì thay>"`.
Phần đầu file có thêm `capture` (thông số màn hình), `forbidden_pages` (trang cấm quay), `global_avoid` (thứ phải che ở mọi cảnh)
và `never_click` (nút cấm bấm).

## 3. Quy trình 5 phút (mọi dạng web app)

Khung kịch bản giống nhau cho mọi app. Nội dung thì sinh theo từng app, chi tiết ở `../references/capture-script-by-app-type.md`:
1. **RECON** (gộp vào bước soát data): Claude mở app ở chế độ chỉ đọc, lập `feature-map.yaml` (`feature-map-template.yaml`).
   File này ghi từng trang: có dữ liệu thật không, "khoảnh khắc wow" là gì, thao tác nào gây ra nó, vùng nhạy cảm, nút nguy hiểm.
   Kèm `web-data-<ngày>.md`. Viết VO xong.
2. **Ghép câu chuyện**: Hook → Vấn đề → 3 chức năng mạnh nhất → Bằng chứng số → CTA, mỗi beat 1 trang có dữ liệu.
   Nháp: `python scripts/capture/capture_log_to_edit.py draft --feature-map feature-map.yaml --out capture-script.yaml`
   (công thức shot theo dạng app: form, dashboard, bảng, AI chat, editor, website, nhiều bước, mobile) → viết câu VO, chỉnh giờ.
   Claude viết giúp: *"viết kịch bản quay chi tiết cho <web>"*.
3. Kiểm (cổng G0): `python scripts/capture/capture_log_to_edit.py lint --script capture-script.yaml --web-data footage/web-data-<ngày>.md`
   → phải ra `G0 PASS`. Lỗi hay gặp: số không có trong web-data (vd gõ nhầm 909%), zoom > 1.5, trang cấm, bấm Lưu, trang không có số (nghi trang trống).
4. Khách xem nhanh bảng shot (URL · thao tác · số sẽ lên hình) → gật.
5. Quay: agent làm ĐÚNG từng step và ghi **capture log** (bước 4 dưới đây).

## 4. Capture log: agent quay phải ghi gì

Mỗi thao tác (và mỗi selector trong `camera`/`highlight`/`avoid`) ghi 1 dòng JSON vào `footage/capture-log.jsonl`, lấy NGAY lúc thao tác:
```json
{"shot":"s01-hook","step":2,"action":"click","t_epoch":1790394946.12,"selector":"input[name=price]",
 "bbox":{"x":300,"y":236,"w":180,"h":34},"viewport":{"w":1536,"h":808},"dpr":1.25,"scrollY":0}
```
- `bbox` = vị trí phần tử trên trang (`getBoundingClientRect`), `t_epoch` = giờ máy (`Date.now()/1000`), cùng đồng hồ với `markers.txt`.
- Đoạn JavaScript lấy dòng này: `python scripts/capture/capture_log_to_edit.py snippet`. Nó hiểu `text=` / `aria=` / `testid=` / `role=`, và khi selector hỏng thì tự tìm theo `fallback_text`.
- Dòng đầu log là `{"event":"rec_start","t_epoch":…}`, hoặc dùng `markers.txt` có dòng `rec_start`.

Sau khi quay, 1 lệnh sinh sẵn dữ liệu dựng, không phải dò hay đoán gì nữa:
```
python scripts/capture/capture_log_to_edit.py build --script capture-script.yaml --log footage/capture-log.jsonl \
       --markers footage/markers.txt --footage data/footage.json --out data/
```
Lệnh ghi ra `data/cursor-path.json` (con trỏ ảo), `data/camera-cues.json` (phóng to vào đâu, ≤ 1.5×, không lộ mép),
`data/highlight-cues.json` (khung, gạch chân, nhãn số) và `data/privacy-boxes.json` (vùng phải che). Toạ độ đã đổi sang toạ độ của footage:
×dpr, trừ dải vàng debugger 70 px.

## 5. Ai làm gì

| Việc | Người | Claude |
|---|---|---|
| Chốt số demo sẽ gõ (vd tốc độ bán = 5, không phải 30) | duyệt | đề xuất trong kịch bản |
| Viết kịch bản + lint G0 | — | làm |
| Kiểm khung chat / trang không trống trước khi quay | — | làm, đọc trang trước |
| Quay đúng kịch bản + ghi log | không đụng máy | làm |
