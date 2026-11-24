"""Kiểm tra giao diện DHShop bằng Edge; ảnh xem trước không ghi vào báo cáo."""

import json
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

BASE_URL = "http://127.0.0.1:8000"
PREVIEW_DIR = Path(__file__).resolve().parent.parent / "preview"
PREVIEW_DIR.mkdir(exist_ok=True)


def run_checks():
    errors = []
    checked_pages = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, locale="vi-VN")
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "response",
            lambda response: (
                errors.append(f"HTTP {response.status}: {response.url}")
                if response.status >= 400
                else None
            ),
        )

        def open_page(path, screenshot=None):
            response = page.goto(BASE_URL + path, wait_until="networkidle")
            assert response.status == 200, (path, response.status)
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), path
            # Ảnh lazy-load bên dưới sẽ được kiểm tra khi cuộn đến từng thẻ.
            for image in page.locator("img").all():
                image.scroll_into_view_if_needed()
                expect(image).to_have_js_property("complete", True)
                assert image.evaluate("(element) => element.naturalWidth > 0"), path
            page.evaluate("window.scrollTo(0, 0)")
            if screenshot:
                page.screenshot(path=str(PREVIEW_DIR / screenshot), full_page=True)
            checked_pages.append(path)

        open_page("/", "trang-chu-desktop.png")
        assert page.locator(".catalog-card").count() == 8

        # Tìm kiếm thật bằng ô tìm kiếm mới trong header.
        page.locator("#search-toggle").click()
        page.locator("#site-search").fill("Essential")
        with page.expect_navigation(wait_until="networkidle"):
            page.locator("#search-panel button[type=submit]").click()
        expect(page.locator(".catalog-card")).to_have_count(1)
        expect(page.locator(".catalog-card h3")).to_contain_text("Essential")

        open_page("/?sort=gia_tang")
        prices = page.locator(".catalog-price > span").all_text_contents()
        values = [
            int("".join(character for character in price if character.isdigit()))
            for price in prices
        ]
        assert values == sorted(values)

        open_page("/danh-muc/ao-thun/")
        assert page.locator(".catalog-card").count() == 2
        page.locator(".quick-add button").first.click()
        expect(page.locator(".cart-count")).to_have_text("1")
        expect(page.locator("#cart-toast")).to_be_visible()

        open_page("/san-pham/so-mi-chambray-xanh/", "chi-tiet-san-pham.png")
        page.locator('[data-quantity-step="1"]').click()
        expect(page.locator("[name=so_luong]")).to_have_value("2")
        page.locator("button[name=hanh_dong][value=mua_ngay]").click()
        page.wait_for_url("**/gio-hang/")
        open_page("/gio-hang/", "gio-hang.png")
        expect(page.locator(".cart-line")).to_have_count(2)

        page.locator('a[href="/gio-hang/thanh-toan/"]').click()
        page.wait_for_url("**/dang-nhap/**")
        page.locator("[name=email]").fill("demo@dhshop.example")
        page.locator("[name=mat_khau]").fill("Dhshop@2026")
        page.locator(".auth-panel button[type=submit]").click()
        page.wait_for_url("**/gio-hang/thanh-toan/")
        open_page("/gio-hang/thanh-toan/", "dat-hang.png")
        page.locator("[name=ten_khach_hang]").fill("Khách hàng demo")
        page.locator("[name=so_dien_thoai]").fill("0901234567")
        page.locator("[name=dia_chi_giao_hang]").fill("Đà Nẵng")
        page.locator(".order-summary button[type=submit]").click()
        page.wait_for_url("**/dat-hang-thanh-cong/**")
        open_page(page.url.removeprefix(BASE_URL))
        expect(page.locator(".cart-count")).to_have_text("0")
        open_page("/khach-hang/lich-su-don-hang/")
        open_page("/khach-hang/tai-khoan/")
        open_page("/khach-hang/dang-ky/")
        open_page("/gioi-thieu/")
        open_page("/lien-he/")

        # Kiểm tra menu, tìm kiếm và bố cục trên điện thoại.
        page.set_viewport_size({"width": 390, "height": 844})
        open_page("/", "trang-chu-mobile.png")
        page.locator(".menu-toggle").click()
        expect(page.locator("#mobile-menu")).to_be_visible()
        page.locator("#mobile-menu a").filter(has_text="Câu chuyện DHShop").click()
        page.wait_for_url("**/gioi-thieu/")
        for path in ["/san-pham/so-mi-chambray-xanh/", "/gio-hang/", "/khach-hang/tai-khoan/"]:
            open_page(path)

        assert not errors, errors
        browser.close()

    result = {"checked_pages": checked_pages, "errors": errors}
    (PREVIEW_DIR / "results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Browser passed: {len(checked_pages)} page visits; no image, HTTP or JavaScript errors.")


if __name__ == "__main__":
    run_checks()
