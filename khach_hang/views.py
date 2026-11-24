from hashlib import sha256

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from gio_hang.models import DonHang
from django.db import IntegrityError, transaction
from .forms import DangKyForm, ThongTinLienHeForm
from .models import HoSoKhachHang


def ma_noi_bo_tu_email(email):
    return "email_" + sha256(email.encode("utf-8")).hexdigest()


def thong_bao_loi_form(request, form):
    for ten_truong, cac_loi in form.errors.items():
        nhan = form.fields[ten_truong].label if ten_truong in form.fields else "Thông tin"
        for loi in cac_loi:
            messages.error(request, f"{nhan}: {loi}")


def dang_ky(request):
    """Trang đăng ký tài khoản khách hàng mới"""
    if request.user.is_authenticated:
        return redirect("khach_hang:lich_su_don_hang")

    form = DangKyForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        email = data["email"]
        # Khóa nội bộ duy nhất để hai lần đăng ký cùng email không tạo hai tài khoản.
        ma_tai_khoan = ma_noi_bo_tu_email(email)
        try:
            # Tài khoản và hồ sơ phải cùng lưu thành công hoặc cùng rollback.
            with transaction.atomic():
                user = User.objects.create_user(
                    username=ma_tai_khoan,
                    email=email,
                    password=data["mat_khau"],
                    first_name=data["ho_ten"],
                )
                user.ho_so.so_dien_thoai = data["so_dien_thoai"]
                user.ho_so.dia_chi = data["dia_chi"]
                user.ho_so.save()
        except IntegrityError:
            form.add_error(
                "email", "Không thể tạo tài khoản. Vui lòng kiểm tra email và thử lại."
            )
        else:
            login(request, user)
            messages.success(request, "Bạn đã đăng ký tài khoản thành công!")
            return redirect("cua_hang:trang_chu")

    if request.method == "POST":
        thong_bao_loi_form(request, form)
    return render(request, "khach_hang/dang_ky.html", {"du_lieu": request.POST, "form": form})


def dang_nhap(request):
    """Trang đăng nhập tài khoản khách hàng"""
    if request.user.is_authenticated:
        return redirect("khach_hang:lich_su_don_hang")

    tiep_tuc = request.POST.get("next") or request.GET.get("next", "")

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        mat_khau = request.POST.get("mat_khau", "")

        user = authenticate(request, email=email, password=mat_khau)

        if user is not None:
            login(request, user)
            messages.success(request, f"Chào mừng trở lại, {user.first_name or user.email}!")
            next_url = request.POST.get("next", "")
            if not url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                next_url = "cua_hang:trang_chu"
            return redirect(next_url)
        else:
            messages.error(request, "Email hoặc mật khẩu không chính xác!")
            return render(
                request,
                "khach_hang/dang_nhap.html",
                {"email": email, "next": tiep_tuc},
            )

    return render(request, "khach_hang/dang_nhap.html", {"next": tiep_tuc})


@require_POST
def dang_xuat(request):
    """Đăng xuất tài khoản khách hàng"""
    logout(request)
    messages.info(request, "Bạn đã đăng xuất thành công khỏi hệ thống.")
    return redirect("cua_hang:trang_chu")


@login_required(login_url="khach_hang:dang_nhap")
def lich_su_don_hang(request):
    """Trang xem lịch sử các đơn hàng và hóa đơn của khách hàng đang đăng nhập"""
    cac_don_hang = (
        DonHang.objects.filter(khach_hang=request.user)
        .prefetch_related("danh_sach_san_pham_dat")
        .order_by("-ngay_tao")
    )
    tong_tien_da_mua = sum(dh.tong_tien for dh in cac_don_hang)

    context = {
        "cac_don_hang": cac_don_hang,
        "tong_so_don": cac_don_hang.count(),
        "tong_tien_da_mua": tong_tien_da_mua,
    }
    return render(request, "khach_hang/lich_su_don_hang.html", context)


@login_required(login_url="khach_hang:dang_nhap")
def chi_tiet_hoa_don(request, ma_don_hang):
    """Xem chi tiết một hóa đơn cụ thể của khách hàng"""
    don_hang = get_object_or_404(DonHang, id=ma_don_hang, khach_hang=request.user)
    return render(request, "khach_hang/chi_tiet_hoa_don.html", {"don_hang": don_hang})


@login_required(login_url="khach_hang:dang_nhap")
def thong_tin_tai_khoan(request):
    """Trang xem và cập nhật thông tin cá nhân của khách hàng"""
    user = request.user
    ho_so, _ = HoSoKhachHang.objects.get_or_create(user=user)

    du_lieu_cu = {
        "ho_ten": user.first_name,
        "email": user.email,
        "so_dien_thoai": ho_so.so_dien_thoai,
        "dia_chi": ho_so.dia_chi,
    }
    form = ThongTinLienHeForm(
        request.POST if request.method == "POST" else None,
        initial=du_lieu_cu,
        user=user,
    )
    if request.method == "POST":
        if form.is_valid():
            data = form.cleaned_data
            try:
                with transaction.atomic():
                    tai_khoan = User.objects.select_for_update().get(pk=user.pk)
                    if tai_khoan.username == ma_noi_bo_tu_email(tai_khoan.email):
                        tai_khoan.username = ma_noi_bo_tu_email(data["email"])
                    tai_khoan.first_name = data["ho_ten"]
                    tai_khoan.email = data["email"]
                    tai_khoan.save(update_fields=["first_name", "email", "username"])
                    ho_so.so_dien_thoai = data["so_dien_thoai"]
                    ho_so.dia_chi = data["dia_chi"]
                    ho_so.save(update_fields=["so_dien_thoai", "dia_chi"])
            except IntegrityError:
                form.add_error("email", "Không thể lưu email này. Vui lòng kiểm tra và thử lại.")
            else:
                messages.success(request, "Cập nhật thông tin tài khoản thành công!")
                return redirect("khach_hang:thong_tin_tai_khoan")
        thong_bao_loi_form(request, form)

    return render(request, "khach_hang/thong_tin_tai_khoan.html", {"ho_so": ho_so, "form": form})
