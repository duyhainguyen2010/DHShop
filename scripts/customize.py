"""Chuyển bản tham khảo thành DHShop; chạy một lần sau khi sao chép mã nguồn."""
from pathlib import Path

root = Path(__file__).resolve().parent.parent
for path in list((root / 'templates').rglob('*.html')) + [root / 'dhshop/urls.py']:
    text = path.read_text(encoding='utf-8')
    text = text.replace('Fashion Store', 'DHShop').replace('FASHION STORE', 'DHS​HOP'.replace('\u200b', ''))
    text = text.replace('>FASHION</span>', '>DH</span>').replace('>STORE</span>', '>Shop</span>')
    text = text.replace('contact@fashionstore.vn', 'contact@dhshop.example')
    path.write_text(text, encoding='utf-8')

for name in ['cua_hang/admin.py', 'gio_hang/admin.py']:
    path = root / name
    text = path.read_text(encoding='utf-8')
    for label in ['Chưa có ảnh', 'Không có ảnh', 'Trống']:
        text = text.replace(f"format_html('<span style=\"color: #999;\">{label}</span>')",
                            f"format_html('<span style=\"color: #999;\">{{}}</span>', '{label}')")
    if name.startswith('gio_hang'):
        text = text.replace('from django.utils.html import format_html', 'from django.utils.html import format_html, format_html_join')
        start = text.index('        dong_html = []')
        end = text.index('    danh_sach_san_pham_dat_mua.short_description', start)
        text = text[:start] + '''        return format_html_join('',
            '<div>• <strong>{}</strong> <span>Size: {}</span> <strong>x{}</strong></div>',
            ((item.ten_san_pham, item.kich_co, item.so_luong) for item in items))
''' + text[end:]
    path.write_text(text, encoding='utf-8')

# Không giữ mật khẩu kết nối có sẵn trong bản tham khảo.
reference_settings = root / 'source-reference/fashion_store/settings.py'
reference_settings.write_text((root / 'dhshop/settings.py').read_text(encoding='utf-8'), encoding='utf-8')
print('DHShop branding and admin fixes ready.')
