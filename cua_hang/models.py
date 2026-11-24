from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class DanhMuc(models.Model):
    """Bảng lưu Danh mục sản phẩm (Áo sơ mi, Áo polo, Quần tây, Váy đầm...)"""

    ten_danh_muc = models.CharField(max_length=100, verbose_name="Tên danh mục")
    slug = models.SlugField(
        max_length=120, unique=True, blank=True, verbose_name="Đường dẫn tĩnh (Slug)"
    )
    mo_ta = models.TextField(blank=True, verbose_name="Mô tả danh mục")
    hinh_anh = models.ImageField(
        upload_to="danh_muc/", blank=True, null=True, verbose_name="Hình ảnh đại diện"
    )

    class Meta:
        verbose_name = "Danh mục"
        verbose_name_plural = "1. Quản lý Danh Mục Sản Phẩm"
        ordering = ["ten_danh_muc"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.ten_danh_muc)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.ten_danh_muc

    def get_absolute_url(self):
        return reverse("cua_hang:san_pham_theo_danh_muc", args=[self.slug])


class SanPham(models.Model):
    """Bảng lưu thông tin Sản phẩm thời trang"""

    danh_muc = models.ForeignKey(
        DanhMuc, on_delete=models.CASCADE, related_name="san_phams", verbose_name="Danh mục"
    )
    ten_san_pham = models.CharField(max_length=200, verbose_name="Tên sản phẩm")
    slug = models.SlugField(
        max_length=220, unique=True, blank=True, verbose_name="Đường dẫn tĩnh (Slug)"
    )
    hinh_anh = models.ImageField(
        upload_to="san_pham/", blank=True, null=True, verbose_name="Ảnh sản phẩm"
    )
    gia_ban = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(0)],
        verbose_name="Giá bán hiện tại (VNĐ)",
    )
    gia_goc = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        verbose_name="Giá niêm yết cũ (VNĐ)",
    )
    mo_ta = models.TextField(verbose_name="Mô tả chi tiết sản phẩm")
    kich_co = models.CharField(
        max_length=100,
        default="S, M, L, XL",
        verbose_name="Các kích cỡ (Size - cách nhau bằng dấu phẩy)",
    )
    mau_sac = models.CharField(
        max_length=100,
        default="Trắng, Đen, Xanh",
        verbose_name="Các màu sắc (cách nhau bằng dấu phẩy)",
    )
    so_luong_kho = models.PositiveIntegerField(default=50, verbose_name="Số lượng tồn kho")
    noi_bat = models.BooleanField(default=False, verbose_name="Sản phẩm nổi bật / Bán chạy")
    dang_kinh_doanh = models.BooleanField(
        default=True, verbose_name="Đang kinh doanh (Hiển thị lên web)"
    )
    ngay_tao = models.DateTimeField(auto_now_add=True, verbose_name="Ngày đăng")
    ngay_cap_nhat = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    class Meta:
        verbose_name = "Sản phẩm"
        verbose_name_plural = "2. Quản lý Sản Phẩm Thời Trang"
        ordering = ["-ngay_tao"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.ten_san_pham)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.ten_san_pham

    def clean(self):
        super().clean()
        loi = {}
        if self.gia_goc is not None and self.gia_ban is not None:
            if self.gia_goc < self.gia_ban:
                loi["gia_goc"] = (
                    "Giá gốc phải lớn hơn hoặc bằng giá bán. Để trống nếu không giảm giá."
                )
        for ten_truong, gioi_han, nhan in [("kich_co", 20, "kích cỡ"), ("mau_sac", 50, "màu sắc")]:
            cac_gia_tri = [
                gia_tri.strip()
                for gia_tri in (getattr(self, ten_truong) or "").split(",")
                if gia_tri.strip()
            ]
            if not cac_gia_tri:
                loi[ten_truong] = f"Nhập ít nhất một {nhan}."
            elif any(len(gia_tri) > gioi_han for gia_tri in cac_gia_tri):
                loi[ten_truong] = (
                    f"Mỗi {nhan} tối đa {gioi_han} ký tự để lưu vào chi tiết đơn hàng."
                )
        if loi:
            raise ValidationError(loi)

    @property
    def anh_dai_dien(self):
        """Dùng ảnh đầu trong bộ ảnh nếu quản trị chưa đặt ảnh đại diện."""
        if self.hinh_anh:
            return self.hinh_anh
        anh_dau = next(iter(self.anh_bo_sung.all()), None)
        return anh_dau.hinh_anh if anh_dau else None

    @property
    def bo_anh(self):
        """Ảnh đại diện đứng trước, ảnh bổ sung theo thứ tự quản trị đã chọn."""
        danh_sach = []
        if self.hinh_anh:
            danh_sach.append({"url": self.hinh_anh.url, "mo_ta": self.ten_san_pham})
        for anh in self.anh_bo_sung.all():
            danh_sach.append(
                {
                    "url": anh.hinh_anh.url,
                    "mo_ta": anh.chu_thich or self.ten_san_pham,
                }
            )
        return danh_sach

    def get_absolute_url(self):
        return reverse("cua_hang:chi_tiet_san_pham", args=[self.slug])

    def danh_sach_kich_co(self):
        """Tách chuỗi kích cỡ thành danh sách để render radio button chọn size"""
        if self.kich_co:
            return [s.strip() for s in self.kich_co.split(",") if s.strip()] or ["Freesize"]
        return ["Freesize"]

    def danh_sach_mau_sac(self):
        """Tách chuỗi màu sắc thành danh sách để render radio button chọn màu"""
        if self.mau_sac:
            return [m.strip() for m in self.mau_sac.split(",") if m.strip()] or ["Tiêu chuẩn"]
        return ["Tiêu chuẩn"]

    @property
    def phan_tram_giam_gia(self):
        """Tự động tính phần trăm giảm giá nếu có giá gốc cũ"""
        if self.gia_goc and self.gia_goc > self.gia_ban:
            return int(((self.gia_goc - self.gia_ban) / self.gia_goc) * 100)
        return 0


class AnhSanPham(models.Model):
    """Một sản phẩm có nhiều ảnh chụp, tách riêng để dễ thêm và sắp xếp."""

    san_pham = models.ForeignKey(
        SanPham, on_delete=models.CASCADE, related_name="anh_bo_sung", verbose_name="Sản phẩm"
    )
    hinh_anh = models.ImageField(upload_to="san_pham/bo_anh/", verbose_name="Ảnh bổ sung")
    chu_thich = models.CharField(max_length=200, blank=True, verbose_name="Chú thích ảnh")
    thu_tu = models.PositiveIntegerField(default=0, verbose_name="Thứ tự")

    class Meta:
        verbose_name = "Ảnh bổ sung"
        verbose_name_plural = "Ảnh bổ sung của sản phẩm"
        ordering = ["thu_tu", "id"]

    def __str__(self):
        return self.chu_thich or f"Ảnh của {self.san_pham.ten_san_pham}"
