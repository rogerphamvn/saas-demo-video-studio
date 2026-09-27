# Privacy checklist — quay tài khoản THẬT mà không lộ gì

Mặc định là CHE — khách không cần nhắc. Che TẠI NGUỒN (script làm sạch trong trang, trước khi quay) tốt hơn che khi dựng.

## Trước khi quay (bước 01–04)
- [ ] Danh sách trang **CẤM quay** (quản trị, phân quyền, billing, trang nội bộ) → `forbidden_pages` trong capture-script.
- [ ] Khách xác nhận **được để lộ** tên dữ liệu demo + số thật hay phải đổi.
- [ ] Dữ liệu demo: chỉ tạo bản ghi mang tiền tố `Demo · …` khi khách cho phép ghi; không sửa/xoá dữ liệu cũ.
      Trang trống (empty state) → không quay; nếu cần nói tới → thẻ chữ trên ảnh chụp mờ.
- [ ] Tắt widget onboarding / chat nổi / toaster; zoom trình duyệt 100%; F11; chỉ Chrome trên màn hình.
- [ ] `never_click`: mọi nút ghi DB (Lưu, Xoá, Gửi, Áp dụng, Tạo…) trừ bước khách đã duyệt.
- [ ] Soát KHUNG CHAT/AI trước: nút "cuộc trò chuyện mới" có thể không tạo phiên mới → lịch sử cũ lộ phía trên.

## Script làm sạch trong trang (cấu hình theo app — `scripts/capture/js/`)
| Thứ phải che | Cách |
|---|---|
| Email, tên tài khoản, avatar ở sidebar/header | ẩn phần tử + thay chữ "<Product> Demo" |
| Lời chào có tên tài khoản | thay chữ THEO TEXT NODE (React tách chuỗi thành nhiều node) |
| Badge vai trò (Super Admin, Owner…), mục ADMIN/Hệ thống | ẩn khối nhóm |
| Tên vendor/model AI trong app | cắt đuôi chữ / ẩn |
| Ghi chú dev, badge NEW, nút chat nổi | ẩn |
| Bản ghi cũ không thuộc demo (tên lô/SKU/khách cũ) | regex tên cũ → ẩn dòng; nhãn trục chart → để trống chữ |
| Dropdown liệt kê dữ liệu cũ | chọn OFF-CAMERA trước `rec_start`, hoặc ẩn option không bắt đầu "Demo ·" |
| Thanh "đang gỡ lỗi trình duyệt" của extension | `crop_top` khi dựng |
| Tên khách/số điện thoại trong đơn | tránh quay; buộc phải có → box che |

Kiểm sau mỗi lần tiêm: `get_page_text` từng route KHÔNG còn chuỗi cấm (email · vai trò · "admin" · tên model · tên cũ).
Reload cứng xoá script → tiêm lại.

## Sau khi quay / sau khi dựng
- [ ] Sheet 0,5 fps cả ca quay: 0 email, 0 tên tài khoản, 0 trang cấm, 0 cửa sổ/thông báo lạ.
- [ ] Sheet 1 fps bản render (cả 16:9 và 9:16 — 9:16 dùng full khung nên có thể lộ phần 16:9 đã crop; clip có crop là LUẬT
      thì đưa vào `keepCrop`).
- [ ] Không để 2 nhãn mâu thuẫn cho cùng 1 số trong 1 khung (nhãn app vs nhãn đồ hoạ).
- [ ] Sau ca: trả trang về trạng thái cũ (gỡ script, bỏ theme/zoom đã đổi); ghi lại mọi dữ liệu demo đã tạo để khách tự quyết giữ/xoá.
