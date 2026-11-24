from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from .models import HoSoKhachHang


class ThongTinTaiKhoanTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="admin",
            password="matkhau123",
            is_staff=True,
        )
        self.user.ho_so.delete()
        self.client.force_login(self.user)

    def test_admin_khong_co_ho_so_van_mo_duoc_trang_cai_dat(self):
        response = self.client.get(reverse("khach_hang:thong_tin_tai_khoan"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(HoSoKhachHang.objects.filter(user=self.user).exists())

    def test_admin_khong_co_ho_so_van_luu_duoc_thong_tin(self):
        response = self.client.post(
            reverse("khach_hang:thong_tin_tai_khoan"),
            {
                "ho_ten": "Quản trị viên",
                "email": "admin@example.com",
                "so_dien_thoai": "0900000000",
                "dia_chi": "Thành phố Hồ Chí Minh",
            },
        )

        self.assertRedirects(
            response,
            reverse("khach_hang:thong_tin_tai_khoan"),
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Quản trị viên")
        self.assertEqual(self.user.email, "admin@example.com")
        self.user.ho_so.refresh_from_db()
        self.assertEqual(self.user.ho_so.so_dien_thoai, "0900000000")
        self.assertEqual(self.user.ho_so.dia_chi, "Thành phố Hồ Chí Minh")

    def test_thong_tin_sai_khong_ghi_de_ho_so(self):
        du_lieu_sai = [
            {"ho_ten": "A" * 151},
            {"email": "email-khong-hop-le"},
            {"so_dien_thoai": "abc"},
            {"so_dien_thoai": "1" * 21},
        ]
        for data in du_lieu_sai:
            with self.subTest(data=data):
                response = self.client.post(reverse("khach_hang:thong_tin_tai_khoan"), data)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["form"].errors)
                self.user.refresh_from_db()
                self.assertEqual(self.user.first_name, "")
                self.assertEqual(self.user.email, "")

    def test_khong_lay_email_cua_tai_khoan_khac(self):
        User.objects.create_user("khac", email="other@example.com")
        response = self.client.post(
            reverse("khach_hang:thong_tin_tai_khoan"), {"email": "OTHER@example.com"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.context["form"].errors)


class DangKyVaDangNhapTests(TestCase):
    def setUp(self):
        self.url = reverse("khach_hang:dang_ky")
        self.data = {
            "ho_ten": "Khách mới",
            "email": "new@example.com",
            "so_dien_thoai": "0901234567",
            "dia_chi": "Đà Nẵng",
            "mat_khau": "MatKhau!2026",
            "xac_nhan_mat_khau": "MatKhau!2026",
        }

    def test_dang_ky_hop_le_tao_ho_so_va_bam_mat_khau(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email=self.data["email"])
        self.assertTrue(user.check_password(self.data["mat_khau"]))
        self.assertNotEqual(user.password, self.data["mat_khau"])
        self.assertEqual(user.ho_so.so_dien_thoai, "0901234567")
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_du_lieu_sai_tra_form_loi_thay_vi_loi_500(self):
        for data_sai in [
            {"email": ""},
            {"ho_ten": "A" * 151},
            {"so_dien_thoai": "1" * 21},
            {"email": "khong-phai-email"},
            {"mat_khau": "12345678", "xac_nhan_mat_khau": "12345678"},
            {"mat_khau": "Ab!12", "xac_nhan_mat_khau": "Ab!12"},
            {"xac_nhan_mat_khau": "khongtrung"},
        ]:
            with self.subTest(data=data_sai):
                response = self.client.post(self.url, {**self.data, **data_sai})
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["form"].errors)
                self.assertFalse(User.objects.exists())

    def test_email_trung_khong_tao_tai_khoan_moi(self):
        User.objects.create_user("daco", email="NEW@example.com")
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.context["form"].errors)
        self.assertEqual(User.objects.count(), 1)

    def test_admin_dang_nhap_bang_email(self):
        admin = User.objects.create_superuser("dhadmin", "admin@example.com", "MatKhau!2026")
        url = reverse("admin:login")

        response = self.client.post(url, {"username": "dhadmin", "password": "MatKhau!2026"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

        response = self.client.post(url, {"username": "ADMIN@example.com", "password": "MatKhau!2026"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(int(self.client.session["_auth_user_id"]), admin.pk)

    def test_giu_duong_dan_dat_hang_sau_khi_dang_nhap_sai(self):
        response = self.client.post(
            reverse("khach_hang:dang_nhap"),
            {
                "email": "khong-co@example.com",
                "mat_khau": "sai",
                "next": reverse("gio_hang:thanh_toan"),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["next"], reverse("gio_hang:thanh_toan"))
