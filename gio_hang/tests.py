from django.contrib.messages import get_messages
from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from cua_hang.models import DanhMuc, SanPham
from .models import ChiTietDonHang, DonHang


class ThemVaoGioTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        danh_muc = DanhMuc.objects.create(
            ten_danh_muc="Áo Thun",
            slug="ao-thun",
        )
        cls.san_pham = SanPham.objects.create(
            danh_muc=danh_muc,
            ten_san_pham="Áo thun kiểm thử",
            slug="ao-thun-kiem-thu",
            gia_ban=100000,
            mo_ta="Sản phẩm kiểm thử",
        )

    def test_them_gio_quay_lai_danh_sach_va_giu_trang_hien_tai(self):
        response = self.client.post(
            reverse("gio_hang:them_vao_gio", args=[self.san_pham.id]),
            {
                "next": "/?page=2#khu-vuc-san-pham",
                "so_luong": "1",
                "kich_co": "M",
                "mau_sac": "Đen",
            },
        )

        self.assertRedirects(
            response,
            "/?page=2#khu-vuc-san-pham",
            fetch_redirect_response=False,
        )

    def test_form_trong_danh_sach_gui_duong_dan_quay_lai_khu_vuc_san_pham(self):
        response = self.client.get(reverse("cua_hang:trang_chu"))
        self.assertRegex(
            response.content.decode(),
            r'name="next"\s+value="/#khu-vuc-san-pham"',
        )

    def test_them_gio_tu_danh_sach_khong_can_tai_lai_trang(self):
        response = self.client.post(
            reverse("gio_hang:them_vao_gio", args=[self.san_pham.id]),
            {
                "so_luong": "1",
                "kich_co": "M",
                "mau_sac": "Đen",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["cart_count"], 1)
        self.assertIn(self.san_pham.ten_san_pham, response.json()["message"])
        self.assertEqual(len(self.client.session["gio_hang"]), 1)
        self.assertEqual(list(get_messages(response.wsgi_request)), [])

    def test_tu_choi_url_quay_lai_ben_ngoai(self):
        response = self.client.post(
            reverse("gio_hang:them_vao_gio", args=[self.san_pham.id]),
            {
                "next": "https://example.com/",
                "so_luong": "1",
                "kich_co": "M",
                "mau_sac": "Đen",
            },
        )

        self.assertRedirects(
            response,
            self.san_pham.get_absolute_url(),
            fetch_redirect_response=False,
        )

    def test_khong_co_url_quay_lai_khong_chuyen_ve_trang_chu(self):
        response = self.client.post(
            reverse("gio_hang:them_vao_gio", args=[self.san_pham.id]),
            {
                "so_luong": "1",
                "kich_co": "M",
                "mau_sac": "Đen",
            },
        )

        self.assertRedirects(
            response,
            self.san_pham.get_absolute_url(),
            fetch_redirect_response=False,
        )

    def test_khach_chua_dang_nhap_duoc_chuyen_den_dang_nhap_de_checkout(self):
        self.client.post(
            reverse("gio_hang:them_vao_gio", args=[self.san_pham.id]),
            {"so_luong": "1", "kich_co": "M", "mau_sac": "Đen"},
        )

        response = self.client.get(reverse("gio_hang:thanh_toan"))

        self.assertRedirects(
            response,
            f"{reverse('khach_hang:dang_nhap')}?next={reverse('gio_hang:thanh_toan')}",
            fetch_redirect_response=False,
        )
        self.assertEqual(len(self.client.session["gio_hang"]), 1)

    def test_khach_chua_dang_nhap_khong_the_tao_don_hang(self):
        self.client.post(
            reverse("gio_hang:them_vao_gio", args=[self.san_pham.id]),
            {"so_luong": "1", "kich_co": "M", "mau_sac": "Đen"},
        )

        response = self.client.post(
            reverse("gio_hang:thanh_toan"),
            {
                "ten_khach_hang": "Khách chưa đăng nhập",
                "so_dien_thoai": "0900000000",
                "dia_chi_giao_hang": "Địa chỉ kiểm thử",
            },
        )

        self.assertEqual(DonHang.objects.count(), 0)
        self.assertEqual(response.status_code, 302)

    def test_dang_nhap_quay_lai_checkout(self):
        user = User.objects.create_user(username="khach", email="khach@example.com", password="matkhau123")

        response = self.client.post(
            f"{reverse('khach_hang:dang_nhap')}?next={reverse('gio_hang:thanh_toan')}",
            {
                "email": user.email.upper(),
                "mat_khau": "matkhau123",
                "next": reverse("gio_hang:thanh_toan"),
            },
        )

        self.assertRedirects(
            response,
            reverse("gio_hang:thanh_toan"),
            fetch_redirect_response=False,
        )

    def test_dang_nhap_tu_choi_next_ben_ngoai(self):
        user = User.objects.create_user(username="khach", email="khach@example.com", password="matkhau123")

        response = self.client.post(
            reverse("khach_hang:dang_nhap"),
            {
                "email": user.email,
                "mat_khau": "matkhau123",
                "next": "https://example.com/",
            },
        )

        self.assertRedirects(
            response,
            reverse("cua_hang:trang_chu"),
            fetch_redirect_response=False,
        )

    def test_dat_hang_tru_ton_kho_va_giu_nguyen_gia_giam(self):
        user = User.objects.create_user(username="khach", password="matkhau123")
        self.client.force_login(user)
        self.san_pham.so_luong_kho = 5
        self.san_pham.gia_goc = 150000
        self.san_pham.save()
        self.client.post(
            reverse("gio_hang:them_vao_gio", args=[self.san_pham.id]),
            {"so_luong": "2", "kich_co": "M", "mau_sac": "Đen"},
        )

        response = self.client.post(
            reverse("gio_hang:thanh_toan"),
            {
                "ten_khach_hang": "Khách kiểm thử",
                "so_dien_thoai": "0900000000",
                "dia_chi_giao_hang": "Địa chỉ kiểm thử",
            },
        )

        self.assertRedirects(
            response,
            reverse("gio_hang:dat_hang_thanh_cong", args=[DonHang.objects.get().pk]),
            fetch_redirect_response=False,
        )
        self.san_pham.refresh_from_db()
        self.assertEqual(self.san_pham.so_luong_kho, 3)
        self.assertEqual(self.san_pham.gia_ban, 100000)
        self.assertEqual(self.san_pham.gia_goc, 150000)
        self.assertEqual(ChiTietDonHang.objects.get().don_gia, 100000)
        self.assertContains(
            self.client.get(self.san_pham.get_absolute_url()),
            "-33%",
        )
        self.assertContains(
            self.client.get(reverse("cua_hang:trang_chu")),
            "-33%",
        )

    def test_khong_tao_don_hoac_tru_kho_khi_ton_kho_khong_du(self):
        user = User.objects.create_user(username="khach", password="matkhau123")
        self.client.force_login(user)
        self.san_pham.so_luong_kho = 1
        self.san_pham.save()
        self.client.post(
            reverse("gio_hang:them_vao_gio", args=[self.san_pham.id]),
            {"so_luong": "2", "kich_co": "M", "mau_sac": "Đen"},
        )

        response = self.client.post(
            reverse("gio_hang:thanh_toan"),
            {
                "ten_khach_hang": "Khách kiểm thử",
                "so_dien_thoai": "0900000000",
                "dia_chi_giao_hang": "Địa chỉ kiểm thử",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "không đủ tồn kho")
        self.assertEqual(DonHang.objects.count(), 0)
        self.san_pham.refresh_from_db()
        self.assertEqual(self.san_pham.so_luong_kho, 1)
        self.assertEqual(len(self.client.session["gio_hang"]), 1)


class ThongKeDoanhThuAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="matkhau123",
        )

    def test_trang_thong_ke_phan_biet_don_huy_va_don_hoan_thanh(self):
        DonHang.objects.create(
            ten_khach_hang="Đơn hoàn thành",
            so_dien_thoai="0900000001",
            dia_chi_giao_hang="Địa chỉ 1",
            tong_tien=200000,
            trang_thai="hoan_thanh",
        )
        DonHang.objects.create(
            ten_khach_hang="Đơn chờ xác nhận",
            so_dien_thoai="0900000002",
            dia_chi_giao_hang="Địa chỉ 2",
            tong_tien=100000,
            trang_thai="cho_xac_nhan",
        )
        DonHang.objects.create(
            ten_khach_hang="Đơn đã hủy",
            so_dien_thoai="0900000003",
            dia_chi_giao_hang="Địa chỉ 3",
            tong_tien=50000,
            trang_thai="da_huy",
        )
        self.client.force_login(self.admin)

        response = self.client.get(reverse("admin:gio_hang_donhang_revenue"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["tong_doanh_thu"], 300000)
        self.assertEqual(response.context["doanh_thu_hoan_thanh"], 200000)
        self.assertEqual(response.context["so_don_hop_le"], 2)
        self.assertEqual(response.context["so_don_da_huy"], 1)
        self.assertEqual(
            response.context["cac_thang"][-1]["doanh_thu"],
            300000,
            response.context["cac_thang"],
        )
        self.assertEqual(response.context["cac_thang"][-1]["so_don"], 2)

    def test_danh_sach_don_hang_co_lien_ket_den_thong_ke(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("admin:gio_hang_donhang_changelist"))

        self.assertContains(response, reverse("admin:gio_hang_donhang_revenue"))

    def test_trang_chu_admin_khong_hien_muc_doanh_thu_rieng(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("admin:index"))

        self.assertNotContains(response, "3. Doanh thu")

    def test_trang_thong_ke_chi_danh_cho_quan_tri(self):
        response = self.client.get(reverse("admin:gio_hang_donhang_revenue"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin:login"), response.url)


class GioHangTestBase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("buyer", password="Dhshop@2026")
        category = DanhMuc.objects.create(ten_danh_muc="Áo", slug="ao")
        self.product = SanPham.objects.create(
            danh_muc=category,
            ten_san_pham="Áo DHShop",
            slug="ao-dhshop",
            gia_ban=100000,
            mo_ta="Áo mẫu",
            so_luong_kho=5,
        )
        self.add_url = reverse("gio_hang:them_vao_gio", args=[self.product.pk])
        self.checkout_url = reverse("gio_hang:thanh_toan")
        self.shipping = {
            "ten_khach_hang": "Khách demo",
            "so_dien_thoai": "0901234567",
            "dia_chi_giao_hang": "Đà Nẵng",
        }

    def add_product(self, quantity="1", **extra):
        return self.client.post(
            self.add_url, {"so_luong": quantity, "kich_co": "M", "mau_sac": "Đen", **extra}
        )

class DHShopRegressionTests(GioHangTestBase):
    def test_invalid_quantities_and_variants_do_not_change_cart(self):
        for quantity in ["abc", "-2", "0", "1000", "1.5"]:
            self.add_product(quantity)
            self.assertFalse(self.client.session.get("gio_hang"))
        self.add_product(kich_co="INVALID")
        self.assertFalse(self.client.session.get("gio_hang"))

    def test_cart_mutations_require_post(self):
        self.assertEqual(self.client.get(self.add_url).status_code, 405)
        self.assertEqual(self.client.get(reverse("gio_hang:cap_nhat_so_luong")).status_code, 405)
        self.assertEqual(
            self.client.get(reverse("gio_hang:xoa_khoi_gio", args=["abc"])).status_code, 405
        )

    def test_csrf_required_for_cart_mutation(self):
        from django.test import Client

        self.assertEqual(Client(enforce_csrf_checks=True).post(self.add_url, {}).status_code, 403)

    def test_hidden_product_cannot_be_ordered_from_existing_cart(self):
        self.client.force_login(self.user)
        self.add_product()
        self.product.dang_kinh_doanh = False
        self.product.save()
        self.assertEqual(self.client.post(self.add_url, {}).status_code, 404)
        response = self.client.post(self.checkout_url, self.shipping)
        self.assertContains(response, "không đủ tồn kho")
        self.assertFalse(DonHang.objects.exists())

    def test_checkout_uses_current_database_price(self):
        self.client.force_login(self.user)
        self.add_product("2")
        self.product.gia_ban = 120000
        self.product.save()
        self.client.post(self.checkout_url, self.shipping)
        order = DonHang.objects.get()
        self.assertEqual(order.tong_tien, 240000)
        self.assertEqual(order.danh_sach_san_pham_dat.get().don_gia, 120000)
        self.assertNotIn("gio_hang", self.client.session)

    def test_other_customer_cannot_open_confirmation_or_invoice(self):
        order = DonHang.objects.create(khach_hang=self.user, **self.shipping)
        other = User.objects.create_user("other", password="Dhshop@2026")
        self.client.force_login(other)
        self.assertEqual(
            self.client.get(reverse("gio_hang:dat_hang_thanh_cong", args=[order.pk])).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(reverse("khach_hang:chi_tiet_hoa_don", args=[order.pk])).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(reverse("gio_hang:in_hoa_don", args=[order.pk])).status_code, 302
        )

    def test_stock_checked_across_sizes(self):
        self.client.force_login(self.user)
        self.add_product("3")
        self.add_product("3", kich_co="L")
        self.client.post(self.checkout_url, self.shipping)
        self.assertFalse(DonHang.objects.exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.so_luong_kho, 5)

    def test_invalid_shipping_does_not_create_order(self):
        self.client.force_login(self.user)
        self.add_product()
        self.client.post(self.checkout_url, {**self.shipping, "so_dien_thoai": "abc"})
        self.assertFalse(DonHang.objects.exists())

    def test_checkout_rolls_back_if_order_item_creation_fails(self):
        from unittest.mock import patch

        self.client.force_login(self.user)
        self.add_product()
        with patch(
            "gio_hang.views.ChiTietDonHang.objects.create", side_effect=RuntimeError("rollback")
        ):
            with self.assertRaises(RuntimeError):
                self.client.post(self.checkout_url, self.shipping)
        self.assertFalse(DonHang.objects.exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.so_luong_kho, 5)
        self.assertTrue(self.client.session.get("gio_hang"))

    def test_san_pham_bi_xoa_khong_lam_ket_gio_hang(self):
        self.client.force_login(self.user)
        self.add_product()
        self.product.delete()
        response = self.client.get(reverse("gio_hang:xem_gio_hang"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.client.session.get("gio_hang"))
        self.assertContains(response, "Giỏ hàng đang chờ")
        self.assertRedirects(self.client.get(self.checkout_url), reverse("cua_hang:trang_chu"))

    def test_size_hoac_mau_da_bi_bo_khong_duoc_dat_tiep(self):
        self.client.force_login(self.user)
        self.add_product()
        self.product.kich_co = "S, L"
        self.product.save()
        response = self.client.post(self.checkout_url, self.shipping)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kích cỡ hoặc màu sắc đã thay đổi")
        self.assertFalse(DonHang.objects.exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.so_luong_kho, 5)

    def test_tong_tien_qua_lon_khong_loi_500_va_khong_tru_kho(self):
        self.client.force_login(self.user)
        self.product.gia_ban = 999999999999
        self.product.save()
        self.add_product("2")
        response = self.client.post(self.checkout_url, self.shipping)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tổng đơn hàng vượt giới hạn")
        self.assertFalse(DonHang.objects.exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.so_luong_kho, 5)

    def test_staff_khong_co_quyen_don_hang_khong_duoc_xem_hoa_don(self):
        order = DonHang.objects.create(khach_hang=self.user, **self.shipping)
        staff = User.objects.create_user("staff_khong_quyen", is_staff=True)
        self.client.force_login(staff)
        response = self.client.get(reverse("gio_hang:in_hoa_don", args=[order.pk]))
        self.assertRedirects(response, reverse("cua_hang:trang_chu"))

    def test_staff_khong_co_quyen_don_hang_khong_duoc_xem_thong_ke(self):
        staff = User.objects.create_user("staff_khong_quyen", is_staff=True)
        self.client.force_login(staff)
        response = self.client.get(reverse("admin:gio_hang_donhang_revenue"))
        self.assertEqual(response.status_code, 403)


class XuLyDonHangTests(GioHangTestBase):
    """Tái dùng bộ dữ liệu mua hàng, chỉ thêm các tình huống quản lý đơn."""

    def tao_don_da_tru_kho(self):
        self.client.force_login(self.user)
        self.add_product("2")
        self.client.post(self.checkout_url, self.shipping)
        self.product.refresh_from_db()
        self.assertEqual(self.product.so_luong_kho, 3)
        return DonHang.objects.get()

    def test_huy_don_hoan_kho_mot_lan_ke_ca_form_cu(self):
        don = self.tao_don_da_tru_kho()
        ban_cu = DonHang.objects.get(pk=don.pk)
        don.trang_thai = "da_huy"
        don.save()
        ban_cu.trang_thai = "da_huy"
        ban_cu.save()
        self.product.refresh_from_db()
        self.assertEqual(self.product.so_luong_kho, 5)

    def test_khong_mo_lai_don_da_huy(self):
        from django.core.exceptions import ValidationError

        don = self.tao_don_da_tru_kho()
        don.trang_thai = "da_huy"
        don.save()
        don.trang_thai = "da_xac_nhan"
        with self.assertRaises(ValidationError):
            don.save()
        don.refresh_from_db()
        self.assertEqual(don.trang_thai, "da_huy")

    def test_khong_huy_don_hoan_thanh_va_khong_lui_trang_thai(self):
        from django.core.exceptions import ValidationError

        don = self.tao_don_da_tru_kho()
        don.trang_thai = "dang_giao"
        don.save()
        don.trang_thai = "cho_xac_nhan"
        with self.assertRaises(ValidationError):
            don.save()
        don.trang_thai = "hoan_thanh"
        don.save()
        don.trang_thai = "da_huy"
        with self.assertRaises(ValidationError):
            don.save()
        self.product.refresh_from_db()
        self.assertEqual(self.product.so_luong_kho, 3)

    def test_admin_huy_don_tu_danh_sach_hoan_kho(self):
        don = self.tao_don_da_tru_kho()
        admin = User.objects.create_superuser("quantri", "admin@example.com", "Test@2026")
        self.client.force_login(admin)
        url = reverse("admin:gio_hang_donhang_changelist")
        data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "1",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-id": str(don.pk),
            "form-0-trang_thai": "da_huy",
            "_save": "Lưu",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.so_luong_kho, 5)
        data["form-0-trang_thai"] = "cho_xac_nhan"
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        don.refresh_from_db()
        self.assertEqual(don.trang_thai, "da_huy")

    def test_admin_khong_tao_don_rong_hoac_xoa_hoa_don(self):
        don = self.tao_don_da_tru_kho()
        admin = User.objects.create_superuser("quantri", "admin@example.com", "Test@2026")
        self.client.force_login(admin)
        self.assertEqual(self.client.get(reverse("admin:gio_hang_donhang_add")).status_code, 403)
        self.assertEqual(
            self.client.get(reverse("admin:gio_hang_donhang_delete", args=[don.pk])).status_code,
            403,
        )
        chi_tiet = don.danh_sach_san_pham_dat.get()
        self.assertEqual(
            self.client.get(
                reverse("admin:gio_hang_chitietdonhang_delete", args=[chi_tiet.pk])
            ).status_code,
            403,
        )

    def test_admin_khong_tu_sua_tong_tien_hoac_chuyen_chu_don(self):
        don = self.tao_don_da_tru_kho()
        admin = User.objects.create_superuser("quantri", "admin@example.com", "Test@2026")
        self.client.force_login(admin)
        chi_tiet = don.danh_sach_san_pham_dat.get()
        response = self.client.post(
            reverse("admin:gio_hang_donhang_change", args=[don.pk]),
            {
                **self.shipping,
                "email": "",
                "ghi_chu": "",
                "trang_thai": "da_xac_nhan",
                "tong_tien": "1",
                "khach_hang": admin.pk,
                "danh_sach_san_pham_dat-TOTAL_FORMS": "1",
                "danh_sach_san_pham_dat-INITIAL_FORMS": "1",
                "danh_sach_san_pham_dat-MIN_NUM_FORMS": "0",
                "danh_sach_san_pham_dat-MAX_NUM_FORMS": "1000",
                "danh_sach_san_pham_dat-0-id": chi_tiet.pk,
                "danh_sach_san_pham_dat-0-don_hang": don.pk,
                "_save": "Lưu",
            },
        )
        self.assertEqual(response.status_code, 302)
        don.refresh_from_db()
        self.assertEqual(don.tong_tien, 200000)
        self.assertEqual(don.khach_hang, self.user)


class MuaHangDongThoiTests(TransactionTestCase):
    """Hai kết nối MySQL thật; không chạy trên database demo của người dùng."""

    def setUp(self):
        from django.db import connection

        self.ten_database_test = connection.settings_dict["NAME"]
        self.user = User.objects.create_user("khach_dong_thoi", password="Test@2026")
        danh_muc = DanhMuc.objects.create(ten_danh_muc="Áo", slug="ao")
        self.product = SanPham.objects.create(
            danh_muc=danh_muc,
            ten_san_pham="Áo cuối",
            slug="ao-cuoi",
            gia_ban=100000,
            so_luong_kho=1,
            mo_ta="Kiểm tra đồng thời",
        )
        self.shipping = {
            "ten_khach_hang": "Khách",
            "so_dien_thoai": "0901234567",
            "dia_chi_giao_hang": "Đà Nẵng",
        }

    def test_hai_khach_cung_mua_san_pham_cuoi_chi_mot_don_thanh_cong(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import connection, connections
        from django.test import Client

        san_sang = Barrier(2)

        def dat_hang():
            try:
                self.assertEqual(connection.settings_dict["NAME"], self.ten_database_test)
                client = Client()
                client.force_login(User.objects.get(pk=self.user.pk))
                client.post(
                    reverse("gio_hang:them_vao_gio", args=[self.product.pk]),
                    {"so_luong": "1", "kich_co": "M", "mau_sac": "Đen"},
                )
                san_sang.wait(timeout=10)
                return client.post(reverse("gio_hang:thanh_toan"), self.shipping).status_code
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(dat_hang), pool.submit(dat_hang)]
            ket_qua = [future.result(timeout=20) for future in futures]
        self.assertEqual(sorted(ket_qua), [200, 302])
        self.assertEqual(DonHang.objects.count(), 1)
        self.product.refresh_from_db()
        self.assertEqual(self.product.so_luong_kho, 0)

    def test_hai_lan_huy_dong_thoi_chi_hoan_kho_mot_lan(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import connection, connections

        self.product.so_luong_kho = 0
        self.product.save()
        don = DonHang.objects.create(khach_hang=self.user, **self.shipping, tong_tien=100000)
        ChiTietDonHang.objects.create(
            don_hang=don,
            san_pham=self.product,
            ten_san_pham=self.product.ten_san_pham,
            don_gia=100000,
            so_luong=1,
        )
        san_sang = Barrier(2)

        def huy_don():
            try:
                self.assertEqual(connection.settings_dict["NAME"], self.ten_database_test)
                ban_cu = DonHang.objects.get(pk=don.pk)
                san_sang.wait(timeout=10)
                ban_cu.trang_thai = "da_huy"
                ban_cu.save()
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(huy_don), pool.submit(huy_don)]
            for future in futures:
                future.result(timeout=20)
        self.product.refresh_from_db()
        self.assertEqual(self.product.so_luong_kho, 1)
