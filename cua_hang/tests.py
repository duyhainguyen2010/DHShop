from decimal import Decimal
from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template import Context, Template
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import AnhSanPham, DanhMuc, SanPham


class DinhDangTienTests(SimpleTestCase):
    def test_hien_thi_vnd_voi_dau_cham_phan_tach_hang_nghin(self):
        template = Template("{% load tien_te %}{{ amount|vnd }}₫")

        self.assertEqual(
            template.render(Context({"amount": Decimal("12345678")})),
            "12.345.678₫",
        )


class PhanTrangSanPhamTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        danh_muc = DanhMuc.objects.create(
            ten_danh_muc="Áo Thun",
            slug="ao-thun",
        )
        SanPham.objects.bulk_create(
            [
                SanPham(
                    danh_muc=danh_muc,
                    ten_san_pham=f"Áo thun {so}",
                    slug=f"ao-thun-{so}",
                    gia_ban=100000 + so,
                    mo_ta="Sản phẩm kiểm thử",
                )
                for so in range(10)
            ]
        )

    def test_moi_trang_chi_hien_toi_da_8_san_pham(self):
        response = self.client.get(reverse("cua_hang:trang_chu"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["san_phams"]), 8)
        self.assertEqual(response.context["trang_hien_tai"].paginator.count, 10)

    def test_trang_ke_tiep_hien_cac_san_pham_con_lai(self):
        response = self.client.get(
            reverse("cua_hang:trang_chu"),
            {"page": 2},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["san_phams"]), 2)
        self.assertEqual(response.context["trang_hien_tai"].number, 2)

    def test_phan_trang_giu_bo_loc_tim_kiem_va_sap_xep(self):
        response = self.client.get(
            reverse("cua_hang:san_pham_theo_danh_muc", args=["ao-thun"]),
            {"q": "áo", "sort": "gia_giam", "page": 2},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["san_phams"]), 2)
        self.assertEqual(response.context["tu_khoa"], "áo")
        self.assertEqual(response.context["sap_xep"], "gia_giam")

    def test_form_sap_xep_quay_lai_khu_vuc_san_pham(self):
        response = self.client.get(reverse("cua_hang:trang_chu"))

        self.assertContains(
            response,
            'action="/#khu-vuc-san-pham"',
        )


class QuanTriSanPhamTests(TestCase):
    """Kiểm tra lưu qua form Admin thật, gồm cả formset ảnh bổ sung."""

    def setUp(self):
        media_tam = TemporaryDirectory()
        self.addCleanup(media_tam.cleanup)
        cau_hinh_media = override_settings(MEDIA_ROOT=media_tam.name)
        cau_hinh_media.enable()
        self.addCleanup(cau_hinh_media.disable)

        self.admin = User.objects.create_superuser("quantri", "admin@example.com", "Test@2026")
        self.client.force_login(self.admin)
        self.danh_muc = DanhMuc.objects.create(ten_danh_muc="Áo", slug="ao")
        self.san_pham = SanPham.objects.create(
            danh_muc=self.danh_muc,
            ten_san_pham="Áo kiểm tra",
            slug="ao-kiem-tra",
            gia_ban=400000,
            mo_ta="Sản phẩm kiểm thử quản trị",
            hinh_anh=self.tao_anh("dai-dien.png"),
        )
        self.url_sua = reverse("admin:cua_hang_sanpham_change", args=[self.san_pham.pk])

    @staticmethod
    def tao_anh(ten_tep):
        noi_dung = BytesIO()
        Image.new("RGB", (40, 50), color="beige").save(noi_dung, format="PNG")
        return SimpleUploadedFile(ten_tep, noi_dung.getvalue(), content_type="image/png")

    def du_lieu_form(self, **thay_doi):
        cac_anh = list(self.san_pham.anh_bo_sung.all())
        data = {
            "ten_san_pham": self.san_pham.ten_san_pham,
            "slug": self.san_pham.slug,
            "danh_muc": self.danh_muc.pk,
            "mo_ta": self.san_pham.mo_ta,
            "gia_ban": "400000",
            "gia_goc": "",
            "kich_co": "S, M, L",
            "mau_sac": "Trắng, Đen",
            "so_luong_kho": "15",
            "dang_kinh_doanh": "on",
            "anh_bo_sung-TOTAL_FORMS": str(len(cac_anh)),
            "anh_bo_sung-INITIAL_FORMS": str(len(cac_anh)),
            "anh_bo_sung-MIN_NUM_FORMS": "0",
            "anh_bo_sung-MAX_NUM_FORMS": "1000",
            "_save": "Lưu",
        }
        for index, anh in enumerate(cac_anh):
            data[f"anh_bo_sung-{index}-id"] = anh.pk
            data[f"anh_bo_sung-{index}-san_pham"] = self.san_pham.pk
            data[f"anh_bo_sung-{index}-chu_thich"] = anh.chu_thich
            data[f"anh_bo_sung-{index}-thu_tu"] = anh.thu_tu
        data.update(thay_doi)
        return data

    def test_ten_san_pham_co_lien_ket_mo_trang_sua(self):
        response = self.client.get(reverse("admin:cua_hang_sanpham_changelist"))
        self.assertContains(response, f'<a href="{self.url_sua}">Áo kiểm tra</a>', html=True)

    def test_luu_gia_giam_va_hien_thi_ra_cua_hang(self):
        response = self.client.post(
            self.url_sua, self.du_lieu_form(gia_goc="400000", gia_ban="320000")
        )
        self.assertEqual(response.status_code, 302)
        self.san_pham.refresh_from_db()
        self.assertEqual(self.san_pham.gia_ban, 320000)
        self.assertEqual(self.san_pham.gia_goc, 400000)
        self.assertEqual(self.san_pham.phan_tram_giam_gia, 20)
        trang_chi_tiet = self.client.get(self.san_pham.get_absolute_url())
        self.assertContains(trang_chi_tiet, "320.000₫")
        self.assertContains(trang_chi_tiet, "400.000₫")
        self.assertContains(trang_chi_tiet, "-20%")

    def test_bo_gia_cu_se_bo_nhan_giam_gia(self):
        self.san_pham.gia_goc = 500000
        self.san_pham.save()
        response = self.client.post(self.url_sua, self.du_lieu_form())
        self.assertEqual(response.status_code, 302)
        self.san_pham.refresh_from_db()
        self.assertIsNone(self.san_pham.gia_goc)
        self.assertEqual(self.san_pham.phan_tram_giam_gia, 0)

    def test_tu_choi_gia_am_va_gia_goc_thap_hon_gia_ban(self):
        for gia_goc, gia_ban in [("400000", "-1"), ("-1", "320000"), ("200000", "320000")]:
            with self.subTest(gia_goc=gia_goc, gia_ban=gia_ban):
                response = self.client.post(
                    self.url_sua, self.du_lieu_form(gia_goc=gia_goc, gia_ban=gia_ban)
                )
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["adminform"].form.errors)
                self.san_pham.refresh_from_db()
                self.assertEqual(self.san_pham.gia_ban, 400000)

    def test_tai_nhieu_anh_khi_sua_san_pham(self):
        data = self.du_lieu_form(
            tai_anh_bo_sung=[self.tao_anh("truoc.png"), self.tao_anh("sau.png")]
        )
        response = self.client.post(self.url_sua, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.san_pham.anh_bo_sung.count(), 2)
        self.assertEqual(len(self.san_pham.bo_anh), 3)
        trang_chi_tiet = self.client.get(self.san_pham.get_absolute_url())
        for anh in self.san_pham.anh_bo_sung.all():
            self.assertContains(trang_chi_tiet, anh.hinh_anh.url)
            self.assertTrue(anh.hinh_anh.storage.exists(anh.hinh_anh.name))
        self.assertContains(trang_chi_tiet, 'data-image-number="3"')

    def test_tai_nhieu_anh_khi_tao_san_pham_moi(self):
        url_tao = reverse("admin:cua_hang_sanpham_add")
        data = self.du_lieu_form(
            slug="ao-moi",
            ten_san_pham="Áo mới",
            tai_anh_bo_sung=[self.tao_anh("moi-1.png"), self.tao_anh("moi-2.png")],
        )
        response = self.client.post(url_tao, data)
        self.assertEqual(response.status_code, 302)
        san_pham_moi = SanPham.objects.get(slug="ao-moi")
        self.assertEqual(san_pham_moi.anh_bo_sung.count(), 2)
        self.assertEqual(san_pham_moi.anh_dai_dien, san_pham_moi.anh_bo_sung.first().hinh_anh)
        self.assertContains(
            self.client.get(reverse("cua_hang:trang_chu")), san_pham_moi.anh_dai_dien.url
        )

    def test_kiem_tra_tung_anh_khong_chi_tep_cuoi(self):
        tep_hong = SimpleUploadedFile("hong.png", b"khong-phai-anh", content_type="image/png")
        response = self.client.post(
            self.url_sua,
            self.du_lieu_form(
                gia_ban="320000",
                tai_anh_bo_sung=[tep_hong, self.tao_anh("hop-le.png")],
            ),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("tai_anh_bo_sung", response.context["adminform"].form.errors)
        self.assertEqual(self.san_pham.anh_bo_sung.count(), 0)
        self.san_pham.refresh_from_db()
        self.assertEqual(self.san_pham.gia_ban, 400000)

    def test_sap_xep_va_xoa_anh_qua_inline(self):
        anh_truoc = AnhSanPham.objects.create(
            san_pham=self.san_pham, hinh_anh=self.tao_anh("mot.png"), thu_tu=1
        )
        anh_sau = AnhSanPham.objects.create(
            san_pham=self.san_pham, hinh_anh=self.tao_anh("hai.png"), thu_tu=2
        )
        data = self.du_lieu_form()
        data["anh_bo_sung-0-thu_tu"] = "9"
        data["anh_bo_sung-1-chu_thich"] = "Mặt sau sản phẩm"
        response = self.client.post(self.url_sua, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            list(self.san_pham.anh_bo_sung.values_list("id", flat=True)), [anh_sau.pk, anh_truoc.pk]
        )
        self.assertEqual(self.san_pham.bo_anh[1]["mo_ta"], "Mặt sau sản phẩm")

        data = self.du_lieu_form()
        data["anh_bo_sung-0-DELETE"] = "on"
        response = self.client.post(self.url_sua, data)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(AnhSanPham.objects.filter(pk=anh_sau.pk).exists())
        self.assertTrue(AnhSanPham.objects.filter(pk=anh_truoc.pk).exists())

    def test_khong_co_quyen_them_anh_thi_khong_tai_duoc_anh(self):
        from django.contrib.auth.models import Permission

        nhan_vien = User.objects.create_user("nhanvien", password="Test@2026", is_staff=True)
        quyen_sua = Permission.objects.get(
            codename="change_sanpham", content_type__app_label="cua_hang"
        )
        nhan_vien.user_permissions.add(quyen_sua)
        self.client.force_login(nhan_vien)
        response = self.client.post(
            self.url_sua, self.du_lieu_form(tai_anh_bo_sung=[self.tao_anh("khong-quyen.png")])
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.san_pham.anh_bo_sung.count(), 0)

    def test_khong_luu_size_hoac_mau_khong_the_ghi_vao_don_hang(self):
        for data_sai in [{"kich_co": "X" * 21}, {"mau_sac": "X" * 51}, {"kich_co": ",,,"}]:
            with self.subTest(data=data_sai):
                response = self.client.post(self.url_sua, self.du_lieu_form(**data_sai))
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["adminform"].form.errors)
