"""Form quản trị sản phẩm và kiểm tra từng tệp trong lần tải nhiều ảnh."""

from django import forms

from .models import SanPham


class ChonNhieuAnh(forms.ClearableFileInput):
    allow_multiple_selected = True


class TruongNhieuAnh(forms.ImageField):
    widget = ChonNhieuAnh

    def clean(self, data, initial=None):
        if not data:
            return []
        cac_tep = data if isinstance(data, (list, tuple)) else [data]
        kiem_tra_mot_anh = super().clean
        return [kiem_tra_mot_anh(tep, initial) for tep in cac_tep]


class SanPhamAdminForm(forms.ModelForm):
    tai_anh_bo_sung = TruongNhieuAnh(
        label="Thêm nhiều ảnh",
        required=False,
        widget=ChonNhieuAnh(attrs={"accept": "image/*"}),
        help_text="Giữ Ctrl hoặc Shift để chọn nhiều ảnh. Các ảnh đang có vẫn được giữ lại.",
    )

    class Meta:
        model = SanPham
        fields = "__all__"
        labels = {"hinh_anh": "Ảnh đại diện"}
        help_texts = {
            "hinh_anh": "Ảnh dùng trên danh sách sản phẩm. Nếu để trống, dùng ảnh bổ sung đầu tiên.",
            "gia_goc": "Giá trước khi giảm, ví dụ 400000. Để trống khi không có giá cũ.",
            "gia_ban": "Giá khách thanh toán, ví dụ 320000. Nhập số liền, không có dấu chấm hoặc chữ đ.",
        }
