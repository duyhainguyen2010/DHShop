# Đọc code DHShop từ đâu?

Mã chạy thực tế nằm ở thư mục gốc. Thư mục `source-reference/` chỉ để tham khảo; sửa file trong đó sẽ không thay đổi website.

## 1. Ba thành phần MVT

| Thành phần | File ví dụ | Đọc để hiểu |
| --- | --- | --- |
| Model | `cua_hang/models.py` | Danh mục và sản phẩm được lưu như thế nào |
| View | `cua_hang/views.py` | Nhận yêu cầu, lọc sản phẩm, chuyển dữ liệu sang HTML |
| Template | `templates/cua_hang/danh_sach_san_pham.html` | Hiển thị dữ liệu view đã cung cấp |
| URL | `cua_hang/urls.py` | Địa chỉ nào gọi hàm view nào |

Ví dụ xem chi tiết sản phẩm:

```text
/san-pham/so-mi-chambray-xanh/
    → dhshop/urls.py              Chuyển yêu cầu sang app cửa hàng
    → cua_hang/urls.py            Chọn hàm chi_tiet_san_pham
    → cua_hang/views.py           Tìm SanPham qua ORM
    → templates/cua_hang/chi_tiet_san_pham.html
    → Trả HTML về trình duyệt
```

## 2. Muốn sửa giao diện

| Cần sửa | File |
| --- | --- |
| Khung chung, header, footer, menu | `templates/bo_cuc_chung.html` |
| Banner, danh mục bên trái, danh sách sản phẩm | `templates/cua_hang/danh_sach_san_pham.html` |
| Một thẻ sản phẩm | `templates/cua_hang/_the_san_pham.html` |
| Chi tiết sản phẩm | `templates/cua_hang/chi_tiet_san_pham.html` |
| Bộ ảnh và dãy ảnh nhỏ | `templates/cua_hang/_bo_anh_san_pham.html` |
| Đăng ký/đăng nhập | `templates/khach_hang/dang_ky.html`, `dang_nhap.html` |
| Giỏ và đặt hàng | `templates/gio_hang/chi_tiet_gio_hang.html`, `thanh_toan.html` |
| Màu, font, header/footer, nút chung | `static/css/base.css` |
| Bố cục trang chủ và sản phẩm | `static/css/cua-hang.css` |
| Form, tài khoản, giỏ, checkout | `static/css/tai-khoan-va-gio-hang.css` |
| Giao diện điện thoại | `static/css/responsive.css` |
| Tìm kiếm, thêm nhanh vào giỏ, nút +/- | `static/js/dhshop.js` |
| Bấm ảnh nhỏ để đổi ảnh lớn | `static/js/product-gallery.js` |

Các template kế thừa `bo_cuc_chung.html`. Chỉ viết nội dung riêng trong `{% block content %}`; không chép lại header và footer vào từng trang. Thẻ sản phẩm dùng `{% include %}` để danh sách và phần sản phẩm liên quan dùng cùng một cấu trúc.

CSS dùng các biến `--paper`, `--cream`, `--cocoa`, `--ink`, `--line` trong `base.css`. Muốn đổi tông màu, sửa các biến này trước. Các class như `catalog-grid`, `detail-layout`, `order-summary` được đặt theo vai trò của phần giao diện.

Ảnh sản phẩm: `SanPham.hinh_anh` giữ ảnh đại diện; model `AnhSanPham` giữ các ảnh bổ sung, chú thích và thứ tự. Property `bo_anh` ghép thành danh sách cho template, property `anh_dai_dien` chọn ảnh thay thế khi thiếu ảnh chính. `cua_hang/forms.py` kiểm tra từng tệp tải lên, `admin.py` lưu chúng và cung cấp inline để sắp xếp/xóa. `views.py` tải sẵn quan hệ ảnh bằng `prefetch_related` để tránh truy vấn lặp theo từng ảnh.

## 3. Muốn hiểu giỏ hàng và đặt hàng

1. `gio_hang/xu_ly_gio_hang.py`: lớp `GioHang` lưu lựa chọn trong session. Khóa của mỗi dòng gồm mã sản phẩm + size + màu.
2. `gio_hang/views.py`: các hàm thêm/sửa/xóa giỏ và `thanh_toan`.
3. `gio_hang/models.py`: `DonHang` lưu người nhận/tổng tiền; `ChiTietDonHang` lưu từng sản phẩm và giá lúc mua.
4. `gio_hang/admin.py`: cách người quản trị xem và xử lý đơn.

Luồng `thanh_toan`: kiểm tra đăng nhập → đọc giỏ → kiểm tra thông tin nhận → mở transaction → khóa sản phẩm → kiểm tra tồn → tạo đơn và chi tiết → trừ kho → kết thúc transaction → làm trống giỏ.

## 4. Quy tắc khi sửa

- Python dùng 4 dấu cách, tên hàm/biến nói rõ mục đích.
- Template chỉ hiển thị dữ liệu; kiểm tra và tính tiền ở phía Python.
- Không đổi tên trường model tùy tiện; thay schema cần migration.
- Không lưu mật khẩu database trực tiếp trong code; chỉnh `.env`.
- Form thay đổi dữ liệu dùng POST và `{% csrf_token %}`.
- CSS/JavaScript viết ở file riêng; phần lặp lại tách thành template dùng chung.
- Chú thích giải thích lý do của nghiệp vụ, không chú thích lại từng dòng hiển nhiên.

Sau khi sửa chức năng, chạy `manage.py check` và những bài kiểm thử liên quan. Khi chỉ sửa nội dung hoặc màu sắc, xem lại trang trên trình duyệt, cả máy tính và điện thoại.
