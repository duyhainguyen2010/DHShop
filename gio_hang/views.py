import re
from decimal import Decimal

from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from cua_hang.models import SanPham
from .xu_ly_gio_hang import GioHang
from .models import DonHang, ChiTietDonHang


def xem_gio_hang(request):
    """Trang xem chi tiết giỏ hàng và danh sách món đã chọn"""
    gio = GioHang(request)
    return render(request, "gio_hang/chi_tiet_gio_hang.html", {"gio_hang": gio})


@require_POST
def them_vao_gio(request, ma_san_pham):
    """Thêm sản phẩm với Size và Màu sắc vào giỏ hàng"""
    gio = GioHang(request)
    san_pham = get_object_or_404(SanPham, id=ma_san_pham, dang_kinh_doanh=True)

    if request.method == "POST":
        kich_co = request.POST.get("kich_co") or san_pham.danh_sach_kich_co()[0]
        mau_sac = request.POST.get("mau_sac") or san_pham.danh_sach_mau_sac()[0]
        try:
            so_luong = int(request.POST.get("so_luong", 1))
            gio.them_san_pham(
                san_pham=san_pham, so_luong=so_luong, kich_co=kich_co, mau_sac=mau_sac
            )
        except (ValueError, TypeError):
            message = "Số lượng phải từ 1 đến 999; vui lòng chọn kích cỡ và màu sắc hợp lệ."
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"message": message}, status=400)
            messages.error(request, "Số lượng, kích cỡ hoặc màu sắc không hợp lệ.")
            return redirect(san_pham.get_absolute_url())

        hanh_dong = request.POST.get("hanh_dong")
        if hanh_dong == "mua_ngay":
            messages.success(
                request, f'Đã thêm "{san_pham.ten_san_pham}" (Size: {kich_co}) vào giỏ hàng!'
            )
            return redirect("gio_hang:xem_gio_hang")
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "message": f'Đã thêm "{san_pham.ten_san_pham}" vào giỏ hàng!',
                    "cart_count": len(gio),
                }
            )
        messages.success(
            request, f'Đã thêm "{san_pham.ten_san_pham}" (Size: {kich_co}) vào giỏ hàng!'
        )

    url_quay_lai = request.POST.get("next") or request.META.get("HTTP_REFERER", "")
    if url_has_allowed_host_and_scheme(
        url=url_quay_lai,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(url_quay_lai)
    return redirect(san_pham.get_absolute_url())


@require_POST
def cap_nhat_so_luong(request):
    """Cập nhật số lượng của một món trong giỏ hàng"""
    gio = GioHang(request)
    if request.method == "POST":
        khoa = request.POST.get("khoa")
        so_luong = request.POST.get("so_luong")
        if khoa and so_luong:
            try:
                gio.cap_nhat_so_luong(khoa=khoa, so_luong=int(so_luong))
                messages.info(request, "Đã cập nhật số lượng món đồ trong giỏ.")
            except (ValueError, TypeError):
                messages.error(request, "Số lượng phải là số nguyên từ 1 đến 999.")
    return redirect("gio_hang:xem_gio_hang")


@require_POST
def xoa_khoi_gio(request, khoa):
    """Xóa một món đồ khỏi giỏ hàng"""
    gio = GioHang(request)
    gio.xoa_san_pham(khoa)
    messages.warning(request, "Đã xóa sản phẩm khỏi giỏ hàng.")
    return redirect("gio_hang:xem_gio_hang")


@login_required(login_url="khach_hang:dang_nhap")
def thanh_toan(request):
    """Trang nhập thông tin giao hàng và xác nhận đặt hàng"""
    gio = GioHang(request)
    if len(gio) == 0:
        messages.warning(request, "Giỏ hàng của bạn đang trống!")
        return redirect("cua_hang:trang_chu")

    # Lấy thông tin mặc định nếu khách hàng đã đăng nhập
    thong_tin = {"ten_khach_hang": "", "so_dien_thoai": "", "email": "", "dia_chi_giao_hang": ""}
    if request.user.is_authenticated:
        thong_tin["ten_khach_hang"] = request.user.get_full_name() or request.user.username
        thong_tin["email"] = request.user.email
        if hasattr(request.user, "ho_so"):
            thong_tin["so_dien_thoai"] = request.user.ho_so.so_dien_thoai
            thong_tin["dia_chi_giao_hang"] = request.user.ho_so.dia_chi

    if request.method == "POST":
        ten_khach_hang = request.POST.get("ten_khach_hang", "").strip()
        so_dien_thoai = request.POST.get("so_dien_thoai", "").strip()
        email = request.POST.get("email", "").strip()
        dia_chi_giao_hang = request.POST.get("dia_chi_giao_hang", "").strip()
        ghi_chu = request.POST.get("ghi_chu", "").strip()

        if not ten_khach_hang or not so_dien_thoai or not dia_chi_giao_hang:
            messages.error(
                request, "Vui lòng nhập đầy đủ họ tên, số điện thoại và địa chỉ nhận hàng!"
            )
            return render(
                request, "gio_hang/thanh_toan.html", {"gio_hang": gio, "thong_tin": request.POST}
            )

        try:
            if len(ten_khach_hang) > 100 or not re.fullmatch(r"0[0-9]{9}", so_dien_thoai):
                raise ValidationError(
                    "Họ tên tối đa 100 ký tự; số điện thoại gồm 10 chữ số, bắt đầu bằng 0."
                )
            if email:
                validate_email(email)
                if len(email) > 254:
                    raise ValidationError("Email không được dài quá 254 ký tự.")
        except ValidationError as error:
            messages.error(request, " ".join(error.messages))
            return render(
                request, "gio_hang/thanh_toan.html", {"gio_hang": gio, "thong_tin": request.POST}
            )

        khach_hang_user = request.user if request.user.is_authenticated else None

        with transaction.atomic():
            so_luong_theo_san_pham = {}
            for item in gio.gio_hang.values():
                ma_san_pham = item["ma_san_pham"]
                so_luong_theo_san_pham[ma_san_pham] = (
                    so_luong_theo_san_pham.get(ma_san_pham, 0) + item["so_luong"]
                )

            san_phams = (
                SanPham.objects.select_for_update().order_by("pk").in_bulk(so_luong_theo_san_pham)
            )

            het_hang_ids = [
                ma_san_pham
                for ma_san_pham, so_luong in so_luong_theo_san_pham.items()
                if ma_san_pham not in san_phams
                or san_phams[ma_san_pham].so_luong_kho < so_luong
                or not san_phams[ma_san_pham].dang_kinh_doanh
            ]
            if het_hang_ids:
                ten_san_pham = ", ".join(
                    (
                        san_phams[ma_san_pham].ten_san_pham
                        if ma_san_pham in san_phams
                        else str(ma_san_pham)
                    )
                    for ma_san_pham in het_hang_ids
                )
                messages.error(
                    request,
                    f"Sản phẩm không đủ tồn kho hoặc không còn kinh doanh: {ten_san_pham}. "
                    "Vui lòng kiểm tra lại giỏ hàng.",
                )
                return render(
                    request,
                    "gio_hang/thanh_toan.html",
                    {"gio_hang": gio, "thong_tin": request.POST},
                )

            # Chụp tên/giá từ chính những hàng đang khóa, không dùng cache giỏ trước giao dịch.
            cac_mon_dat = []
            tong_tien = Decimal("0")
            for item in gio.gio_hang.values():
                san_pham = san_phams[item["ma_san_pham"]]
                if (
                    item["kich_co"] not in san_pham.danh_sach_kich_co()
                    or item["mau_sac"] not in san_pham.danh_sach_mau_sac()
                ):
                    messages.error(
                        request,
                        "Kích cỡ hoặc màu sắc đã thay đổi. Vui lòng xóa món đó khỏi giỏ và chọn lại.",
                    )
                    return render(
                        request,
                        "gio_hang/thanh_toan.html",
                        {"gio_hang": gio, "thong_tin": request.POST},
                    )
                cac_mon_dat.append({**item, "san_pham": san_pham, "don_gia": san_pham.gia_ban})
                tong_tien += san_pham.gia_ban * item["so_luong"]

            if tong_tien > Decimal("999999999999"):
                messages.error(
                    request,
                    "Tổng đơn hàng vượt giới hạn xử lý. Vui lòng giảm số lượng hoặc chia nhỏ đơn.",
                )
                return render(
                    request,
                    "gio_hang/thanh_toan.html",
                    {"gio_hang": gio, "thong_tin": request.POST},
                )

            don_hang = DonHang.objects.create(
                khach_hang=khach_hang_user,
                ten_khach_hang=ten_khach_hang,
                so_dien_thoai=so_dien_thoai,
                email=email,
                dia_chi_giao_hang=dia_chi_giao_hang,
                ghi_chu=ghi_chu,
                tong_tien=tong_tien,
            )

            for item in cac_mon_dat:
                ChiTietDonHang.objects.create(
                    don_hang=don_hang,
                    san_pham=item["san_pham"],
                    ten_san_pham=item["san_pham"].ten_san_pham,
                    don_gia=item["don_gia"],
                    so_luong=item["so_luong"],
                    kich_co=item["kich_co"],
                    mau_sac=item["mau_sac"],
                )

            for ma_san_pham, so_luong in so_luong_theo_san_pham.items():
                san_pham = san_phams[ma_san_pham]
                san_pham.so_luong_kho -= so_luong
                san_pham.save(update_fields=["so_luong_kho"])

        # Cập nhật địa chỉ mặc định cho khách nếu chưa có
        if request.user.is_authenticated and hasattr(request.user, "ho_so"):
            if not request.user.ho_so.so_dien_thoai and so_dien_thoai:
                request.user.ho_so.so_dien_thoai = so_dien_thoai
            if not request.user.ho_so.dia_chi and dia_chi_giao_hang:
                request.user.ho_so.dia_chi = dia_chi_giao_hang
            request.user.ho_so.save()

        gio.lam_trong_gio()
        return redirect("gio_hang:dat_hang_thanh_cong", ma_don_hang=don_hang.id)

    return render(request, "gio_hang/thanh_toan.html", {"gio_hang": gio, "thong_tin": thong_tin})


@login_required(login_url="khach_hang:dang_nhap")
def dat_hang_thanh_cong(request, ma_don_hang):
    """Trang hiển thị thông báo đặt hàng thành công của khách"""
    don_hang = get_object_or_404(DonHang, id=ma_don_hang, khach_hang=request.user)
    return render(request, "gio_hang/dat_hang_thanh_cong.html", {"don_hang": don_hang})


@login_required(login_url="khach_hang:dang_nhap")
def in_hoa_don(request, ma_don_hang):
    """Trang xem và in phiếu hóa đơn chuẩn đẹp cho Admin và Khách hàng"""
    don_hang = get_object_or_404(DonHang, id=ma_don_hang)
    # Quyền xem: Admin/Staff hoặc chính khách hàng sở hữu đơn
    co_quyen_quan_tri = request.user.is_staff and (
        request.user.has_perm("gio_hang.view_donhang")
        or request.user.has_perm("gio_hang.change_donhang")
    )
    if not co_quyen_quan_tri and don_hang.khach_hang != request.user:
        messages.error(request, "Bạn không có quyền xem hóa đơn này!")
        return redirect("cua_hang:trang_chu")

    return render(request, "gio_hang/in_hoa_don.html", {"don_hang": don_hang})
