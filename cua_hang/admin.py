from copy import deepcopy

from django.contrib import admin
from django.db.models import Max
from django.utils.html import format_html

from .formatters import format_vnd
from .forms import SanPhamAdminForm
from .models import AnhSanPham, DanhMuc, SanPham


@admin.register(DanhMuc)
class DanhMucAdmin(admin.ModelAdmin):
    list_display = ["anh_dai_dien", "ten_danh_muc", "slug", "so_san_pham"]
    list_display_links = ["anh_dai_dien", "ten_danh_muc"]
    prepopulated_fields = {"slug": ("ten_danh_muc",)}
    search_fields = ["ten_danh_muc"]

    def anh_dai_dien(self, obj):
        if obj.hinh_anh:
            return format_html(
                '<img src="{}" style="width: 45px; height: 45px; object-fit: cover; border-radius: 6px;" />',
                obj.hinh_anh.url,
            )
        return format_html('<span style="color: #999;">{}</span>', "Chưa có ảnh")

    anh_dai_dien.short_description = "Ảnh"

    def so_san_pham(self, obj):
        return f"{obj.san_phams.count()} sản phẩm"

    so_san_pham.short_description = "Số lượng SP"


class AnhSanPhamInline(admin.TabularInline):
    model = AnhSanPham
    extra = 1
    fields = ["xem_truoc", "hinh_anh", "chu_thich", "thu_tu"]
    readonly_fields = ["xem_truoc"]

    @admin.display(description="Xem trước")
    def xem_truoc(self, obj):
        if obj and obj.hinh_anh:
            return format_html(
                '<img src="{}" alt="{}" width="75" height="90" style="object-fit: cover;">',
                obj.hinh_anh.url,
                obj.chu_thich or "Ảnh sản phẩm",
            )
        return "Chưa chọn ảnh"


@admin.register(SanPham)
class SanPhamAdmin(admin.ModelAdmin):
    form = SanPhamAdminForm
    inlines = [AnhSanPhamInline]
    list_display_links = ["anh_san_pham", "ten_san_pham"]
    list_display = [
        "anh_san_pham",
        "ten_san_pham",
        "danh_muc",
        "gia_ban_vnd",
        "gia_goc_vnd",
        "muc_giam_gia",
        "so_luong_kho",
        "noi_bat",
        "dang_kinh_doanh",
        "ngay_tao",
    ]
    list_filter = ["danh_muc", "dang_kinh_doanh", "noi_bat", "ngay_tao"]
    list_editable = ["so_luong_kho", "noi_bat", "dang_kinh_doanh"]
    prepopulated_fields = {"slug": ("ten_san_pham",)}
    search_fields = ["ten_san_pham", "mo_ta", "danh_muc__ten_danh_muc"]
    list_per_page = 20
    readonly_fields = ["muc_giam_gia"]
    fieldsets = [
        (
            "Thông tin sản phẩm",
            {
                "fields": ["ten_san_pham", "slug", "danh_muc", "mo_ta"],
            },
        ),
        (
            "Giá bán và giảm giá",
            {
                "fields": ["gia_goc", "gia_ban", "muc_giam_gia"],
                "description": "Ví dụ: giá gốc 400000, giá bán 320000 → giảm 20%. Bấm Lưu để áp dụng.",
            },
        ),
        ("Hình ảnh", {"fields": ["hinh_anh", "tai_anh_bo_sung"]}),
        ("Lựa chọn và tồn kho", {"fields": ["kich_co", "mau_sac", "so_luong_kho"]}),
        ("Hiển thị", {"fields": ["noi_bat", "dang_kinh_doanh"]}),
    ]

    def get_queryset(self, request):
        return (
            super().get_queryset(request).select_related("danh_muc").prefetch_related("anh_bo_sung")
        )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        truong_anh = form.base_fields.get("tai_anh_bo_sung")
        if truong_anh:
            # Không thay đổi field dùng chung giữa các tài khoản quản trị.
            truong_anh = deepcopy(truong_anh)
            truong_anh.disabled = not request.user.has_perm("cua_hang.add_anhsanpham")
            form.base_fields["tai_anh_bo_sung"] = truong_anh
        return form

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        cac_anh_moi = form.cleaned_data.get("tai_anh_bo_sung", [])
        thu_tu_cuoi = form.instance.anh_bo_sung.aggregate(lon_nhat=Max("thu_tu"))["lon_nhat"]
        for vi_tri, tep_anh in enumerate(cac_anh_moi, start=(thu_tu_cuoi or 0) + 1):
            AnhSanPham.objects.create(san_pham=form.instance, hinh_anh=tep_anh, thu_tu=vi_tri)

    @admin.display(description="Mức giảm giá")
    def muc_giam_gia(self, obj):
        if not obj or not obj.phan_tram_giam_gia:
            return "Không giảm giá"
        return f"{obj.phan_tram_giam_gia}%"

    def anh_san_pham(self, obj):
        if obj.anh_dai_dien:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 6px;" />',
                obj.anh_dai_dien.url,
            )
        return format_html('<span style="color: #999;">{}</span>', "Chưa có ảnh")

    anh_san_pham.short_description = "Ảnh"

    def gia_ban_vnd(self, obj):
        gia_str = f"{format_vnd(obj.gia_ban)}₫"
        return format_html('<strong style="color: #dc3545;">{}</strong>', gia_str)

    gia_ban_vnd.short_description = "Giá bán"

    def gia_goc_vnd(self, obj):
        if obj.gia_goc:
            return f"{format_vnd(obj.gia_goc)}₫"
        return "-"

    gia_goc_vnd.short_description = "Giá gốc"
