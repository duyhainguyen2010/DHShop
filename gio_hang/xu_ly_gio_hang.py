from decimal import Decimal
from cua_hang.models import SanPham


class GioHang:
    """Lớp xử lý giỏ hàng lưu trong Session của người dùng"""

    def __init__(self, request):
        self.session = request.session
        gio_hang = self.session.get("gio_hang")
        if not gio_hang:
            gio_hang = self.session["gio_hang"] = {}
        self.gio_hang = gio_hang
        self._bang_san_pham = None

    def _doc_san_pham(self):
        """Tải một lần mỗi request, bỏ món đã bị xóa để giỏ không bị mắc kẹt."""
        if self._bang_san_pham is None:
            cac_id = [item["ma_san_pham"] for item in self.gio_hang.values()]
            san_phams = SanPham.objects.filter(id__in=cac_id).prefetch_related("anh_bo_sung")
            self._bang_san_pham = {sp.id: sp for sp in san_phams}
            for khoa, item in list(self.gio_hang.items()):
                if item["ma_san_pham"] not in self._bang_san_pham:
                    del self.gio_hang[khoa]
                    self.luu()
        return self._bang_san_pham

    def _tao_khoa_san_pham(self, ma_san_pham, kich_co, mau_sac):
        kc = (kich_co or "M").strip().lower()
        ms = (mau_sac or "Tiêu chuẩn").strip().lower()
        return f"{ma_san_pham}_{kc}_{ms}"

    def them_san_pham(
        self, san_pham, so_luong=1, kich_co="M", mau_sac="Đen", ghi_de_so_luong=False
    ):
        so_luong = int(so_luong)
        if not 1 <= so_luong <= 999:
            raise ValueError("Số lượng phải từ 1 đến 999.")
        if (
            kich_co not in san_pham.danh_sach_kich_co()
            or mau_sac not in san_pham.danh_sach_mau_sac()
        ):
            raise ValueError("Kích cỡ hoặc màu sắc không hợp lệ.")
        khoa = self._tao_khoa_san_pham(san_pham.id, kich_co, mau_sac)
        if not ghi_de_so_luong and self.gio_hang.get(khoa, {}).get("so_luong", 0) + so_luong > 999:
            raise ValueError("Số lượng tối đa là 999.")
        if khoa not in self.gio_hang:
            self.gio_hang[khoa] = {
                "ma_san_pham": san_pham.id,
                "gia": str(san_pham.gia_ban),
                "so_luong": 0,
                "kich_co": kich_co,
                "mau_sac": mau_sac,
            }

        if ghi_de_so_luong:
            self.gio_hang[khoa]["so_luong"] = int(so_luong)
        else:
            self.gio_hang[khoa]["so_luong"] += int(so_luong)

        if self._bang_san_pham is not None:
            self._bang_san_pham[san_pham.id] = san_pham

        if self.gio_hang[khoa]["so_luong"] <= 0:
            self.xoa_san_pham(khoa)
        else:
            self.luu()

    def cap_nhat_so_luong(self, khoa, so_luong):
        if not 1 <= int(so_luong) <= 999:
            raise ValueError("Số lượng phải từ 1 đến 999.")
        if khoa in self.gio_hang:
            sl = int(so_luong)
            if sl > 0:
                self.gio_hang[khoa]["so_luong"] = sl
            else:
                del self.gio_hang[khoa]
            self.luu()

    def xoa_san_pham(self, khoa):
        if khoa in self.gio_hang:
            del self.gio_hang[khoa]
            self.luu()

    def luu(self):
        self.session.modified = True

    def lam_trong_gio(self):
        self.gio_hang.clear()
        self._bang_san_pham = {}
        if "gio_hang" in self.session:
            del self.session["gio_hang"]
            self.luu()

    def __iter__(self):
        bang_san_pham = self._doc_san_pham()

        for khoa, item in self.gio_hang.items():
            san_pham = bang_san_pham.get(item["ma_san_pham"])
            if san_pham:
                don_gia = san_pham.gia_ban
                thanh_tien = don_gia * item["so_luong"]
                yield {
                    "khoa": khoa,
                    "san_pham": san_pham,
                    "don_gia": don_gia,
                    "so_luong": item["so_luong"],
                    "kich_co": item.get("kich_co", "M"),
                    "mau_sac": item.get("mau_sac", ""),
                    "thanh_tien": thanh_tien,
                }

    def __len__(self):
        self._doc_san_pham()
        return sum(item["so_luong"] for item in self.gio_hang.values())

    def tong_tien(self):
        return sum((item["thanh_tien"] for item in self), Decimal("0"))
