"""Kiểm tra dữ liệu tài khoản phía máy chủ, kể cả khi bỏ qua kiểm tra HTML."""

from django import forms
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password


class DangNhapAdminForm(AdminAuthenticationForm):
    username = forms.EmailField(
        label="Email",
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "username", "autofocus": True}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Form gốc lấy giới hạn ký tự từ trường username của model User.
        self.fields["username"].max_length = 254
        self.fields["username"].widget.attrs["maxlength"] = 254


class ThongTinLienHeForm(forms.Form):
    ho_ten = forms.CharField(label="Họ và tên", max_length=150, required=False)
    email = forms.EmailField(label="Email", max_length=254, required=False)
    so_dien_thoai = forms.RegexField(
        label="Số điện thoại",
        regex=r"^0[0-9]{9}$",
        max_length=10,
        required=False,
        error_messages={"invalid": "Nhập 10 chữ số, bắt đầu bằng 0."},
    )
    dia_chi = forms.CharField(label="Địa chỉ", required=False)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user:
            self.fields["email"].required = True

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if email:
            tai_khoan = User.objects.filter(email__iexact=email)
            if self.user:
                tai_khoan = tai_khoan.exclude(pk=self.user.pk)
            if tai_khoan.exists():
                raise forms.ValidationError("Email này đã được dùng bởi tài khoản khác.")
        return email


class DangKyForm(ThongTinLienHeForm):
    email = forms.EmailField(label="Email", max_length=254)
    mat_khau = forms.CharField(label="Mật khẩu", strip=False, widget=forms.PasswordInput)
    xac_nhan_mat_khau = forms.CharField(
        label="Xác nhận mật khẩu", strip=False, widget=forms.PasswordInput
    )

    def clean(self):
        data = super().clean()
        mat_khau = data.get("mat_khau")
        if mat_khau and data.get("xac_nhan_mat_khau"):
            if mat_khau != data["xac_nhan_mat_khau"]:
                self.add_error("xac_nhan_mat_khau", "Mật khẩu xác nhận không trùng khớp.")
            tai_khoan_mau = User(
                email=data.get("email", ""),
                first_name=data.get("ho_ten", ""),
            )
            try:
                validate_password(mat_khau, tai_khoan_mau)
            except forms.ValidationError as error:
                self.add_error("mat_khau", error)
        return data
