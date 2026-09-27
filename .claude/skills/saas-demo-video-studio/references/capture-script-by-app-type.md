# Kịch bản quay cho MỌI dạng web app: khung cố định + nội dung sinh theo từng app

> Câu hỏi của user (26/09): "mỗi web app là một dạng khác thì kịch bản này apply thế nào?"
> Trả lời ngắn: **schema kịch bản giống nhau cho mọi app** (`templates/capture-script-template.yaml`, cổng G0). Phần thay đổi theo app
> là **nội dung**: trang nào, thao tác nào "đắt", số nào lên hình. Nội dung đó sinh ra qua 3 bước: RECON → GHÉP CÂU CHUYỆN → DUYỆT.
> Nguồn: ca ProfitBase (dạng 1, form/máy tính) là ca đo thật DUY NHẤT. Các dạng 2–8 là **mẫu suy ra**, chưa có ca đo. Mỗi dạng
> ghi rõ bẫy nào đã gặp thật, bẫy nào là dự đoán.

## 1. Ba bước sinh kịch bản cho một app bất kỳ

| Bước | Ai | Làm gì | Ra |
|---|---|---|---|
| **1. RECON** (chỉ đọc, ~5′, gộp vào bước "soát data") | agent, dùng Chrome thật đã đăng nhập | Liệt kê route/menu. Với từng trang ghi: có dữ liệu thật không (hay trống / demo USD / 0 đ); **wow_element** (số lớn, biểu đồ, kết quả tức thì); **trigger** (thao tác làm wow xảy ra); vùng nhạy cảm (email, role, admin, API key, chat cũ, tên model AI); nút nguy hiểm (Lưu/Xoá/Gửi/Thanh toán). Số thấy được thì ghi luôn vào web-data | `feature-map.yaml` (`templates/feature-map-template.yaml`) + `web-data-<ngày>.md` |
| **2. GHÉP CÂU CHUYỆN** | agent | Khung **Hook → Vấn đề → 3 chức năng mạnh nhất → Bằng chứng số → CTA** (`templates/vo-script-templates.md`). Mỗi beat chọn 1 route `data_ok: true` trong feature-map (gán trường `beat`). Sinh nháp: `python scripts/capture/capture_log_to_edit.py draft --feature-map feature-map.yaml --out capture-script.draft.yaml` (dùng công thức shot theo dạng app ở §2) → viết `vo_line`, chỉnh thời gian | `capture-script.yaml` |
| **3. DUYỆT** (~5′) | user/khách + cổng G0 | Khách xem bảng shot (URL · thao tác · số lên hình · vùng che) → gật. `capture_log_to_edit.py lint` → **G0 PASS** mới quay | kịch bản chốt |

Luật chọn beat: route `data_ok: false` KHÔNG được gán beat. Cần nói về tính năng đó thì dùng `capture: false` + `replace_with: "thẻ chữ trên ảnh chụp mờ"`,
như montage của ProfitBase (`cut_footage.py:137`: trang module là empty state hoặc dữ liệu USD).

## 2. Thư viện mẫu shot theo dạng app

`app_type` trong feature-map chọn công thức mà lệnh `draft` dùng. Một app có thể có nhiều dạng: đặt `type` riêng cho từng route.

| # | `app_type` | Thao tác "đắt" nhất để quay | Camera / highlight gợi ý | Bẫy hay gặp |
|---|---|---|---|---|
| 1 | `form_calculator`: form, máy tính, cấu hình giá | gõ 1 số, kết quả nhảy real-time (ProfitBase: gõ giá 899000 → cột P&L đổi) | zoom 1.5× ô đang gõ → lướt sang ô kết quả 1.3–1.4×; `spotlight` ô gõ, `callout` số kết quả | **đã gặp:** gõ giá trị chưa chốt ra số xấu (30 → 909%, phải gõ lại 5); lỡ bấm Lưu làm ghi dữ liệu thật (`never_click`) |
| 2 | `dashboard`: analytics, báo cáo | đổi bộ lọc/kỳ → biểu đồ và KPI đổi | mở 1.0× toàn cảnh 1 nhịp, rồi zoom 1.3× vào KPI/biểu đồ vừa đổi; `box` quanh KPI, `underline` con số | **dự đoán:** kỳ mặc định trống ($0 / "No data"), tiền tệ sai (USD), biểu đồ còn đang load lúc quay. ProfitBase `/dashboard` đang 0 đ nên bị loại (timeline s08) |
| 3 | `table_crud`: bảng, danh sách, CRM | tìm/lọc/sắp xếp → mở 1 dòng xem chi tiết | zoom ô tìm → thu về bảng → zoom khung chi tiết; `box` dòng được chọn | **dự đoán:** lộ tên, SĐT, email khách thật trong bảng → cần tài khoản demo hoặc `avoid` cả cột; nút Xoá/Sửa hàng loạt ở cạnh |
| 4 | `ai_chat`: AI chat, trợ lý | gõ câu hỏi → câu trả lời stream → kết luận | zoom ô nhập khi gõ (delay ~60 ms/ký tự) → cắt thời gian chờ khi dựng → zoom kết luận 1.5×; `spotlight` kết luận | **đã gặp:** nút "chat mới" không tạo phiên mới, cuộn lên lộ chat cũ "API key" (action-log #26, #29); tên model AI ở header (PN §7). Precondition: khung chat TRỐNG, kiểm bằng read_page |
| 5 | `editor_canvas`: editor, builder, kéo-thả | kéo 1 khối vào canvas / bấm áp dụng → trước/sau | 1.0× khi kéo (thấy cả nguồn và đích) → zoom 1.3× kết quả; `box` vùng thay đổi | **dự đoán:** kéo-thả bằng extension có thể không ra sự kiện drag thật → thử ở RECON; autosave ghi vào tài liệu của khách → dùng tài liệu nháp |
| 6 | `website_landing`: e-commerce, landing, web công ty (loại C trong GUIDE) | cuộn qua từng section, hover CTA, thêm vào giỏ | cuộn chậm ở 1.0×, zoom 1.2–1.3× tiêu đề section; `underline` câu giá trị, `box` CTA | **dự đoán:** popup cookie/chat widget che nội dung; lazy-load làm ảnh trắng khi cuộn nhanh → cuộn qua 1 lượt trước khi quay; không bấm Thanh toán |
| 7 | `multistep_flow`: onboarding, wizard, tutorial (loại D) | đi từng bước, mỗi bước 1 shot, nhãn "Bước n" | zoom 1.3× trường của bước → nút Tiếp; `callout` "Bước n" | **dự đoán:** bước cuối gửi dữ liệu thật (Gửi/Đăng ký) → dừng trước bước đó; validate lỗi đỏ nếu dữ liệu demo sai định dạng |
| 8 | `mobile_responsive`: bản điện thoại | cùng thao tác của dạng gốc nhưng ở viewport điện thoại | quay viewport ~390×844 (CSS), dựng 9:16 NATIVE (không cần layout chia đôi); zoom ≤ 1.3× | **dự đoán:** `capture.viewport_css` + `dpr` đổi, phải đo lại; menu hamburger che nội dung |

Công thức mà `draft` sinh cho từng dạng nằm trong `scripts/capture/capture_log_to_edit.py` (`RECIPES`). Đó là nháp: người viết phải sửa
thời gian, vo_line và số trước khi chạy lint.

## 3. Selector bền cho mọi app

Thứ tự ưu tiên khi ghi `selector` (agent RECON chọn luôn lúc soát):
1. **Chữ hiển thị**: `text=Lợi nhuận ròng`. Người không kỹ thuật đọc được, ít đổi khi đổi giao diện.
2. **aria-label**: `aria=Tìm kiếm`. **data-testid**: `testid=price-input`. **role + tên**: `role=button:Tiếp tục`.
3. **CSS id/name ổn định**: `#price`, `input[name=price]`.
4. **CSS class**: chỉ khi 3 cách trên không có. Class kiểu `.css-1x2y3z` (sinh tự động) đổi sau mỗi lần build → tránh.
5. **Toạ độ**: phương án CUỐI. Lint báo cảnh báo "selector giòn".

Mỗi step/camera/highlight nên có thêm **`fallback_text`**: chữ để agent tìm lại phần tử khi selector hỏng (app vừa đổi giao diện).
Đoạn JS lấy bbox (đầu `scripts/capture/capture_log_to_edit.py`) hiểu các tiền tố `text=`, `aria=`, `testid=`, `role=` và tự thử
`fallback_text` khi selector không trả về phần tử nào. Log ghi lại selector đã dùng thật (`selector_used`).

## 4. Dữ liệu demo theo dạng app

Việc chung cho mọi dạng: 3–5 bản ghi ĐẸP (số dương, dễ hiểu), đúng tiền tệ (VND ≠ USD), đúng ngôn ngữ, **không trang nào trống**
trong số trang sẽ quay. Số ghi vào web-data lúc RECON.

| Dạng | Cần có sẵn |
|---|---|
| 1 form/máy tính | 1 bản ghi đủ trường. Chốt trước giá trị sẽ gõ và kết quả mong đợi (ghi vào `expected_on_screen`) |
| 2 dashboard | kỳ có dữ liệu (≥ 1 tháng); bộ lọc sẽ đổi phải cho ra số khác 0 |
| 3 bảng/CRUD | 5–10 dòng tên giả nhưng thật-giống; không có PII khách thật |
| 4 AI chat | phiên chat TRỐNG; câu hỏi chốt trước; đã thử 1 lần để biết câu trả lời có số trong web-data |
| 5 editor | tài liệu nháp riêng để kéo-thả; bản "trước" và "sau" |
| 6 website | tắt popup/cookie (chọn từ chối); giỏ hàng trống trước khi quay |
| 7 nhiều bước | dữ liệu hợp lệ cho từng bước; dừng trước bước gửi thật |
| 8 mobile | cùng dữ liệu dạng gốc; kiểm hiển thị ở viewport điện thoại |

**Khi nào xin tài khoản demo RIÊNG** (không quay tài khoản thật của khách):
- trang sẽ quay có dữ liệu cá nhân của người thật (khách hàng, nhân viên) mà che sẽ làm hỏng khung hình;
- cần seed dữ liệu nhưng khách chưa cho phép ghi vào tài khoản thật (ca mẫu: chọn thẻ chữ trên ảnh chụp mờ thay vì seed);
- app có thanh toán, gửi email/SMS thật, hoặc tích hợp bên ngoài chạy khi bấm nút;
- trang chính trống ở tài khoản thật (tài khoản mới, gói dùng thử).
Cần seed mà chưa hỏi khách thì KHÔNG tự seed. Hỏi 1 lượt trong brief (`templates/brief-template.md`).

## 5. Ví dụ ánh xạ: ProfitBase → khung

RECON cho ra: `/batches/.../edit` (dạng 1, `data_ok`), `/boms` (dạng 3; tab Nhà cung cấp trống nên không gán beat), `/compare`
(dạng 2), `/expert` (dạng 4, rủi ro chat cũ), 6 trang module (trống hoặc USD → `capture: false`), `/dashboard` (0 đ → forbidden).
GHÉP: Hook = gõ giá (dạng 1) · Vấn đề/chức năng = P&L, hoà vốn, COGS, phí sàn · Bằng chứng = so sánh 2 lô · CTA = thẻ logo.
Kết quả: `examples/profitbase-capture-script.yaml` (G0 PASS).
