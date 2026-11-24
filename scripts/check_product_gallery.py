"""Kiểm tra lưu giá và nhiều ảnh trên browser bằng một sản phẩm tạm.

Không sửa sản phẩm hiện có; dọn sản phẩm và các ảnh vừa tải sau khi kiểm tra.
Web phải đang chạy ở localhost:8000. Ảnh xem trước được lưu riêng trong preview/.
"""

import os
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dhshop.settings")

import django

django.setup()

from django.conf import settings
from django.core.files.storage import default_storage
from django.urls import reverse
from playwright.sync_api import expect, sync_playwright

from cua_hang.models import DanhMuc, SanPham


def run_checks():
    product = SanPham.objects.create(
        danh_muc=DanhMuc.objects.first(),
        ten_san_pham="Sản phẩm kiểm tra tạm",
        slug="kiem-tra-bo-anh-" + uuid4().hex[:10],
        hinh_anh="dhshop/linen-shirt.jpg",
        gia_ban=400000,
        so_luong_kho=3,
        mo_ta="Sản phẩm được tạo và dọn sau lượt kiểm tra tự động.",
    )
    uploaded_names = set()
    errors = []
    base_url = "http://127.0.0.1:8000"
    preview_dir = ROOT / "preview"
    preview_dir.mkdir(exist_ok=True)

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="msedge", headless=True)
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 1050})
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(base_url + "/admin/login/", wait_until="networkidle")
                page.locator("[name=username]").fill("admin@dhshop.example")
                page.locator("[name=password]").fill("admin123")
                page.locator("input[type=submit]").click()
                page.wait_for_url("**/admin/")

                list_url = reverse("admin:cua_hang_sanpham_changelist")
                page.goto(
                    base_url + list_url + "?q=" + product.ten_san_pham, wait_until="networkidle"
                )
                page.get_by_role("link", name=product.ten_san_pham, exact=True).click()
                page.wait_for_url("**/change/**")
                page.locator("#id_gia_goc").fill("400000")
                page.locator("#id_gia_ban").fill("320000")
                page.locator("#id_tai_anh_bo_sung").set_input_files(
                    [
                        str(ROOT / "media/dhshop/linen-shirt.jpg"),
                        str(ROOT / "media/dhshop/cotton-tee.jpg"),
                    ]
                )
                with page.expect_navigation(wait_until="networkidle"):
                    page.locator("input[name=_save]").click()

                page.goto(base_url + product.get_absolute_url(), wait_until="networkidle")
                expect(page.locator(".detail-pricing")).to_contain_text("320.000₫")
                expect(page.locator(".detail-pricing")).to_contain_text("-20%")
                thumbnails = page.locator("[data-gallery-thumbnail]")
                expect(thumbnails).to_have_count(3)
                expected_url = thumbnails.nth(1).get_attribute("data-image-url")
                thumbnails.nth(1).click()
                expect(page.locator("[data-gallery-main]")).to_have_attribute("src", expected_url)
                expect(page.locator("[data-gallery-position]")).to_have_text("2 / 3")
                thumbnails.nth(2).focus()
                page.keyboard.press("Space")
                expect(thumbnails.nth(2)).to_have_attribute("aria-pressed", "true")
                expect(page.locator("[data-gallery-main]")).to_have_js_property("complete", True)
                assert page.locator("[data-gallery-main]").evaluate(
                    "image => image.naturalWidth > 0"
                )
                page.evaluate("window.scrollTo(0, 0)")
                page.screenshot(
                    path=str(preview_dir / "kiem-tra-bo-anh-desktop.png"), full_page=True
                )

                page.set_viewport_size({"width": 390, "height": 844})
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                thumbnails.first.click()
                expect(page.locator("[data-gallery-position]")).to_have_text("1 / 3")
                page.evaluate("window.scrollTo(0, 0)")
                page.screenshot(
                    path=str(preview_dir / "kiem-tra-bo-anh-mobile.png"), full_page=True
                )
                assert not errors, errors
            finally:
                browser.close()
    finally:
        uploaded_names.update(product.anh_bo_sung.values_list("hinh_anh", flat=True))
        product.delete()
        media_root = Path(settings.MEDIA_ROOT).resolve()
        for name in uploaded_names:
            # Chỉ dọn tệp vừa tạo trong thư mục bộ ảnh của dự án.
            target = (media_root / name).resolve()
            if target.is_relative_to(media_root) and name.startswith("san_pham/bo_anh/"):
                default_storage.delete(name)

    print("Browser passed: admin name link, price saving, multiple upload, gallery and mobile.")


if __name__ == "__main__":
    run_checks()
