"""Tạo dữ liệu demo DHShop. Chạy lại bình thường không ghi đè dữ liệu đã sửa.

Chỉ dùng --refresh-demo khi muốn cập nhật tám sản phẩm mẫu sang bộ sưu tập mới.
"""

import argparse
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dhshop.settings")
django.setup()

from django.contrib.auth.models import User
from django.db import transaction

from cua_hang.models import DanhMuc, SanPham

# slug cũ giúp cập nhật bộ mẫu một lần, giữ nguyên khóa ngoại các đơn đã có.
DANH_MUC_MAU = [
    ("ao-so-mi", "ao-so-mi", "Áo sơ mi"),
    ("ao-thun-polo", "ao-thun", "Áo thun"),
    ("quan-tay-jean", "quan-dai", "Quần dài"),
    ("ao-khoac", "do-det-kim", "Đồ dệt kim"),
    ("vay-dam", "vay-dam", "Váy & đầm"),
]

SAN_PHAM_MAU = [
    {
        "slug_cu": "ao-so-mi-oxford-trang",
        "slug": "so-mi-chambray-xanh",
        "ten_san_pham": "Sơ mi chambray xanh",
        "danh_muc": "ao-so-mi",
        "gia_ban": 359000,
        "gia_goc": 420000,
        "hinh_anh": "dhshop/linen-shirt.jpg",
        "mo_ta": "Sắc xanh dịu và họa tiết nhỏ mang đến một lựa chọn nhẹ nhàng cho ngày thường. Phom sơ mi thoải mái, dễ kết hợp với quần sáng màu hoặc denim.",
        "kich_co": "S, M, L, XL",
        "mau_sac": "Xanh chambray",
    },
    {
        "slug_cu": "ao-thun-unisex-oversize",
        "slug": "ao-thun-essential",
        "ten_san_pham": "Áo thun Essential",
        "danh_muc": "ao-thun",
        "gia_ban": 189000,
        "gia_goc": None,
        "hinh_anh": "dhshop/cotton-tee.jpg",
        "mo_ta": "Chiếc áo thun trắng gọn gàng cho tủ đồ cơ bản. Cổ tròn, tay ngắn và phom dễ mặc, phù hợp để phối riêng hoặc làm lớp áo bên trong.",
        "kich_co": "S, M, L, XL",
        "mau_sac": "Trắng",
    },
    {
        "slug_cu": "ao-polo-nam-phoi-co",
        "slug": "ao-thun-classic",
        "ten_san_pham": "Áo thun Classic",
        "danh_muc": "ao-thun",
        "gia_ban": 219000,
        "gia_goc": 259000,
        "hinh_anh": "dhshop/polo.jpg",
        "mo_ta": "Áo thun cổ tròn với đường nét tối giản. Một lựa chọn thoải mái cho những buổi đi học, dạo phố hay cuối tuần, dễ phối cùng quần dài.",
        "kich_co": "M, L, XL",
        "mau_sac": "Trắng",
    },
    {
        "slug_cu": "quan-tay-nam-ong-dung",
        "slug": "quan-chino-everyday",
        "ten_san_pham": "Quần chino Everyday",
        "danh_muc": "quan-dai",
        "gia_ban": 429000,
        "gia_goc": None,
        "hinh_anh": "dhshop/trousers.jpg",
        "mo_ta": "Quần dài phom gọn với sắc màu dễ phối. Thiết kế hướng đến những bộ trang phục thường ngày, kết hợp cùng áo thun hoặc sơ mi đều tự nhiên.",
        "kich_co": "29, 30, 31, 32, 33",
        "mau_sac": "Be",
    },
    {
        "slug_cu": "quan-jean-nu-ong-loe",
        "slug": "denim-original",
        "ten_san_pham": "Denim Original",
        "danh_muc": "quan-dai",
        "gia_ban": 459000,
        "gia_goc": 520000,
        "hinh_anh": "dhshop/denim.jpg",
        "mo_ta": "Denim xanh với tinh thần mộc mạc, phù hợp với nhiều cách phối đồ. Dễ kết hợp với áo trắng, sơ mi hoặc đồ dệt kim cho một tổng thể giản dị.",
        "kich_co": "S, M, L",
        "mau_sac": "Xanh denim",
    },
    {
        "slug_cu": "ao-so-mi-lua-co-v-nu",
        "slug": "quan-day-rut-rose",
        "ten_san_pham": "Quần bo gấu Rose",
        "danh_muc": "quan-dai",
        "gia_ban": 329000,
        "gia_goc": None,
        "hinh_anh": "dhshop/tailored.jpg",
        "mo_ta": "Sắc hồng đất nhẹ nhàng, phần cạp và gấu quần co giãn tạo vẻ năng động. Phù hợp với áo thun sáng màu để có một bộ trang phục cuối tuần thoải mái.",
        "kich_co": "S, M, L",
        "mau_sac": "Hồng đất",
    },
    {
        "slug_cu": "dam-hoa-nhi-dang-dai",
        "slug": "dam-trang-sunday",
        "ten_san_pham": "Đầm trắng Sunday",
        "danh_muc": "vay-dam",
        "gia_ban": 489000,
        "gia_goc": 560000,
        "hinh_anh": "dhshop/dress.jpg",
        "mo_ta": "Chiếc đầm trắng với cổ trễ vai và chi tiết ren mang cảm hứng những buổi dạo chơi trong nắng. Đường nét nữ tính, nhẹ nhàng và dễ kết hợp cùng phụ kiện tối giản.",
        "kich_co": "S, M, L",
        "mau_sac": "Trắng",
    },
    {
        "slug_cu": "ao-blazer-han-quoc-2-lop",
        "slug": "ao-det-kim-soft",
        "ten_san_pham": "Áo choàng dệt kim Soft",
        "danh_muc": "do-det-kim",
        "gia_ban": 399000,
        "gia_goc": None,
        "hinh_anh": "dhshop/knitwear.jpg",
        "mo_ta": "Bề mặt dệt kim và tông sáng tạo cảm giác ấm áp, dịu mắt. Phom mặc thoải mái cho những ngày thời tiết mát, dễ phối với denim hoặc quần màu trung tính.",
        "kich_co": "S, M, L",
        "mau_sac": "Kem",
    },
]


def tao_tai_khoan_demo():
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser("admin", "admin@dhshop.example", "admin123")

    khach_hang, moi_tao = User.objects.get_or_create(
        username="khachhang1",
        defaults={"first_name": "Khách hàng demo", "email": "demo@dhshop.example"},
    )
    if moi_tao:
        khach_hang.set_password("Dhshop@2026")
        khach_hang.save()
        khach_hang.ho_so.so_dien_thoai = "0901234567"
        khach_hang.ho_so.dia_chi = "Đà Nẵng"
        khach_hang.ho_so.save()


@transaction.atomic
def khoi_tao(cap_nhat_mau=False):
    tao_tai_khoan_demo()
    bang_danh_muc = {}

    for slug_cu, slug, ten in DANH_MUC_MAU:
        danh_muc = DanhMuc.objects.filter(slug=slug).first()
        if danh_muc is None and cap_nhat_mau:
            danh_muc = DanhMuc.objects.filter(slug=slug_cu).first()
        if danh_muc is None:
            danh_muc = DanhMuc.objects.create(slug=slug, ten_danh_muc=ten)
        elif cap_nhat_mau:
            danh_muc.slug = slug
            danh_muc.ten_danh_muc = ten
            danh_muc.save()
        bang_danh_muc[slug] = danh_muc

    for so_thu_tu, du_lieu in enumerate(SAN_PHAM_MAU):
        thong_tin = du_lieu.copy()
        slug_cu = thong_tin.pop("slug_cu")
        thong_tin["danh_muc"] = bang_danh_muc[thong_tin["danh_muc"]]
        thong_tin["noi_bat"] = so_thu_tu < 4
        san_pham = SanPham.objects.filter(slug=thong_tin["slug"]).first()

        if san_pham is None and cap_nhat_mau:
            san_pham = SanPham.objects.filter(slug=slug_cu).first()

        if san_pham is None:
            SanPham.objects.create(**thong_tin, so_luong_kho=30)
        elif cap_nhat_mau:
            # Không ghi đè tồn kho: các đơn đã đặt vẫn cần được giữ nhất quán.
            for ten_truong, gia_tri in thong_tin.items():
                setattr(san_pham, ten_truong, gia_tri)
            san_pham.save()

    print("[DHShop] Du lieu demo san sang. Chay lai khong tao trung san pham.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-demo", action="store_true", help="Cap nhat bo san pham mau.")
    arguments = parser.parse_args()
    khoi_tao(cap_nhat_mau=arguments.refresh_demo)
