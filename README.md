# DHShop

Website bán quần áo bằng **Django · MVT · MySQL**.
Đồ án Công nghệ Web của Nguyễn Duy Hải, Đại học Kiến trúc Đà Nẵng.

Giao diện dùng tông kem và nâu, ảnh minh họa và phông Lora hỗ trợ tiếng Việt. [Xem bản triển khai DHShop](https://dhshop2026-002-site1.ltempurl.com/).

## Chạy trên máy hiện tại

Mở PowerShell trong thư mục dự án:

```powershell
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

- Website: http://127.0.0.1:8000/
- Quản trị: http://127.0.0.1:8000/admin/
- Admin demo trên máy: `admin@dhshop.example` / `admin123`
- Khách demo trên máy: `demo@dhshop.example` / `Dhshop@2026`

Script tự kiểm tra MySQL local, chạy migration, thêm dữ liệu còn thiếu rồi mở Django. Trên máy hiện tại, MySQL riêng chạy cổng 3308 và lưu dữ liệu tại `runtime/mysql/`. Không cần bật Apache. `.env` chứa cấu hình local, không đưa vào Git.

## Cài trên máy khác

Cần Python 3.12 và MySQL 8.0.11 trở lên, khuyến nghị MySQL 8.4.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --isolated -r requirements.txt
Copy-Item .env.example .env
```

Điền tài khoản MySQL thật trong `.env`. Mẫu dùng cổng 3306; dùng cổng đã cấu hình trên máy của bạn.

```powershell
.\.venv\Scripts\python.exe scripts\create_database.py
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe khoi_tao_du_lieu.py
$env:DEBUG='True'
.\.venv\Scripts\python.exe manage.py runserver
```

## Đọc và sửa code

Bắt đầu từ **[HUONG_DAN_MA_NGUON.md](HUONG_DAN_MA_NGUON.md)**.

```text
dhshop/                  Cấu hình project, URL gốc, WSGI/ASGI
cua_hang/                Danh mục, sản phẩm, tìm kiếm và chi tiết
gio_hang/                Giỏ session, đặt hàng, đơn và hóa đơn
khach_hang/              Tài khoản, hồ sơ và lịch sử mua hàng
templates/               Giao diện Django đang chạy
static/css/              CSS chia theo từng phần
static/js/dhshop.js       Tìm kiếm, thêm giỏ nhanh, nút số lượng
static/fonts/lora/       Font và giấy phép OFL
media/dhshop/            Bộ ảnh mới và nguồn ảnh
```

CSS và JavaScript tách khỏi template. `_the_san_pham.html` tái sử dụng thẻ sản phẩm; `_anh_tai_khoan.html` dùng chung ảnh bên cạnh form tài khoản. Tên app và hàm nghiệp vụ bằng tiếng Việt không dấu để dễ đối chiếu bài toán.

## Dữ liệu mẫu

`khoi_tao_du_lieu.py` có 5 danh mục và 8 sản phẩm DHShop. Chạy lại bình thường không ghi đè sản phẩm đã sửa. Lệnh sau chỉ dùng khi muốn chủ động cập nhật toàn bộ thông tin của tám sản phẩm mẫu:

```powershell
.\.venv\Scripts\python.exe khoi_tao_du_lieu.py --refresh-demo
```

Lệnh cập nhật mẫu giữ tồn kho và khóa chính để không làm hỏng liên kết đơn hàng. Ảnh minh họa mới được lưu tại `media/dhshop/`, nguồn trong `sources.json`.

## Kiểm tra và định dạng

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test --noinput
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Các bài kiểm thử dùng database `test_dhshop` riêng do Django tạo/xóa; tài khoản MySQL chạy test cần có quyền tạo database đó.

Cài công cụ phát triển nếu muốn kiểm tra browser hoặc định dạng lại code:

```powershell
.\.venv\Scripts\python.exe -m pip install --isolated -r requirements-dev.txt
.\.venv\Scripts\python.exe scripts\check_interface.py
.\.venv\Scripts\python.exe -m djlint templates --reformat --quiet
.\.venv\Scripts\python.exe -m black --line-length 100 dhshop cua_hang gio_hang khach_hang
```

Kiểm tra browser cần website đang chạy và Microsoft Edge. Script tạo đơn demo thật trong MySQL local và lưu ảnh vào `preview/`, không cập nhật Word.

## Phạm vi hiện tại

- Xem/tìm/lọc/sắp xếp sản phẩm, chọn size/màu, quản lý giỏ.
- Đăng ký và đăng nhập bằng email, cập nhật hồ sơ cá nhân và đăng xuất qua POST.
- Đặt COD; transaction MySQL và kiểm tra tồn kho; lịch sử và hóa đơn.
- Django Admin: sản phẩm, danh mục, tài khoản, hồ sơ, đơn hàng và thống kê.

## Chỉnh giá và thêm nhiều ảnh trong Admin

1. Mở `/admin/cua_hang/sanpham/`, bấm **tên hoặc ảnh sản phẩm** để vào trang sửa.
2. Trong **Giá bán và giảm giá**, nhập giá gốc và giá bán. Ví dụ `400000` và `320000` tương ứng giảm 20%. Xóa giá gốc để bỏ hiển thị giá cũ. Giá không được âm; giá gốc không được thấp hơn giá bán.
3. Trong **Hình ảnh**, đặt ảnh đại diện hoặc dùng ô **Thêm nhiều ảnh** để chọn nhiều tệp cùng lúc (giữ Ctrl/Shift).
4. Phần **Ảnh bổ sung của sản phẩm** bên dưới có ảnh xem trước, chú thích, thứ tự và ô xóa. Số thứ tự nhỏ hơn hiển thị trước. Ảnh đại diện luôn đứng đầu; nếu không đặt ảnh đại diện, dùng ảnh bổ sung đầu tiên.
5. Bấm **Lưu**, mở lại trang sản phẩm. Các ảnh nhỏ cho phép bấm hoặc dùng bàn phím để đổi ảnh lớn.

Thay đổi dữ liệu gồm model `AnhSanPham` (quan hệ nhiều-một với `SanPham`). Chạy `manage.py migrate` khi cập nhật mã sang máy khác. Script `scripts/check_product_gallery.py` kiểm tra thao tác quản trị trên một sản phẩm tạm rồi dọn lại.

Đơn chuyển sang trạng thái hủy được hoàn kho một lần. Website hỗ trợ COD và quản lý tồn kho tổng theo sản phẩm. Trang liên hệ cung cấp thông tin minh họa của đồ án.

Tham khảo khung chức năng MVT từ https://github.com/phannam151001-dau/Cong_nghe_web. Template mua sắm, nhận diện và bộ ảnh đang dùng đã được thay riêng cho DHShop. Django Admin và các nghiệp vụ nền tiếp tục được hoàn thiện trên bản hiện tại.
