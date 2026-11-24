# Đưa DHShop lên SmarterASP.NET Linux

Gói đang chuẩn bị cho Python 3.14, Linux x86_64. Website vẫn dùng Django MVT và MySQL 8.
Thư viện kết nối trên hosting là MySQL Connector/Python chính thức; bản chạy trên máy vẫn dùng mysqlclient.

## 1. Các file đã chuẩn bị

- `hosting-output/DHShop_Linux_Python314.zip`: mã nguồn, ảnh và thư viện Linux; tải vào thư mục `/dhshop` của hosting.
- `hosting-output/private/dhshop_config.json`: cấu hình bí mật lưu trên máy để nhập vào biến môi trường của Python App.
- `hosting-output/private/dhshop_mysql.sql`: schema và sản phẩm; nhập vào database bằng công cụ quản lý MySQL.
- `hosting-output/private/admin.json`: email và mật khẩu quản trị. Điền email vào trường `email` trước khi tạo gói cài mới và lưu file riêng trên máy.

Không đưa thư mục `private`, file SQL hoặc `admin.json` vào `/dhshop`. Gói ZIP không chứa các file này.

## 2. Tải website

1. Trong Files, mở `/dhshop`.
2. Tải `DHShop_Linux_Python314.zip` lên, rồi giải nén tại đây.
3. Kiểm tra thấy trực tiếp `hosting_wsgi.py`, `_vendor`, `dhshop`, `cua_hang`, `templates`, `staticfiles`, `media`.
4. Đổi tên trang mặc định `index.html` thành `index_mac_dinh.html`.
5. Sau khi giải nén xong, xóa file ZIP đã tải lên hosting. Giữ bản ZIP trên máy.

## 3. Cấu hình bí mật

Mở file `hosting-output/private/dhshop_config.json` trên máy.
Thay `DIEN_MAT_KHAU_DATABASE` bằng mật khẩu bạn đã đặt lúc tạo MySQL. Giữ nguyên các thông tin còn lại.
Trong **Website Configuration → Environment Variables** của website `dhshop`, thêm biến `DHSHOP_CONFIG_JSON` bằng **Add or Replace Variable**.
Dán toàn bộ JSON trên một dòng vào ô giá trị. Nếu đã chuẩn bị `hosting-output/private/dhshop_config_env.txt`, dùng nội dung file đó.
Tiến trình Django trên SmarterASP không có quyền đọc file trong thư mục `/private` ngang cấp với website.
Sau khi lưu biến, mở **Python App → Save & Start** để Django nhận cấu hình.
Thư mục `/db` có sẵn chỉ nhận `.sql`, `.bak`, `.backup`; không dùng để lưu cấu hình JSON.
Tên database: `db_ad12f0_dhshop`; người dùng: `ad12f0_dhshop`; server: `mysql5045.site4now.net`.

Nếu sau này thêm tên miền khác, thêm tên miền đó vào danh sách `ALLOWED_HOSTS` rồi restart ứng dụng.

## 4. Nhập MySQL

Vào Databases → MySQL → chọn database `db_ad12f0_dhshop`, mở công cụ quản lý SQL của database.
Nhập file `hosting-output/private/dhshop_mysql.sql` vào database còn trống.
File không có lệnh tạo/xóa database và không chứa đơn hàng, phiên đăng nhập hoặc tài khoản demo cục bộ.
File có cấu trúc bảng, 5 danh mục, 8 sản phẩm hiện tại, quyền Django và một tài khoản quản trị mới.
Không nhập lần hai vào database đã có dữ liệu; không xóa các bảng đang dùng để nhập lại.

## 5. Khởi động Python App

| Ô | Giá trị |
|---|---|
| Python version | Python 3.14 |
| Framework | Django |
| Interface | WSGI |
| Application folder | `.` |
| Startup file | `hosting_wsgi.py` |
| Callable | `application` |

Điểm khởi động đã đổi từ `dhshop/wsgi.py` sang `hosting_wsgi.py` để nạp thư viện đóng gói và cấu hình riêng.
Khi đã hoàn tất bước 2–4, bấm Save & Start.
Mở `https://dhshop2026-002-site1.ltempurl.com/`, đăng nhập `/admin/` bằng email và mật khẩu trong `admin.json` trên máy.
Khi nâng cấp site đang có dữ liệu sang đăng nhập bằng email, gán email cho tài khoản quản trị và các tài khoản chưa có email trước khi chuyển sang bản mới.

## 6. Kiểm tra sau khi chạy

Kiểm tra trang chủ, trang sản phẩm, đăng ký, đăng nhập, giỏ hàng và đặt hàng thử.
Trong admin, sửa giá bán/giá gốc và tải thêm một ảnh sản phẩm, rồi kiểm tra ảnh xuất hiện trên web.
Nếu ứng dụng không chạy, mở View Runtime Logs để lấy lỗi cụ thể. Bộ Pillow đóng gói cần Linux x86_64 dùng glibc 2.28 trở lên.
Các kiểm tra trên máy đã xác nhận 61 test với backend MySQL hosting, nhập SQL vào database mới,
đăng nhập admin và tải trang chủ/CSS/ảnh khi DEBUG=False. Python 3.14 và thư viện ảnh Linux cần kiểm chứng tiếp trên hosting thật.

## Đóng gói lại sau khi sửa web

Chạy `.venv\Scripts\python.exe scripts/build_hosting_package.py` trên máy.
Script giữ nguyên SECRET_KEY và thông tin quản trị đã sinh trước đó.
Khi cập nhật code trên hosting, giữ biến môi trường `DHSHOP_CONFIG_JSON` và ảnh trong `media`.
Không nhập lại SQL vào database đã sử dụng. Thay đổi model sau này cần chạy migration qua môi trường quản trị phù hợp.
