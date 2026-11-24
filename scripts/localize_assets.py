"""Lưu tài nguyên giao diện ở local để demo không phụ thuộc Internet."""
from pathlib import Path
import re
import urllib.request

root = Path(__file__).resolve().parent.parent
vendor = root / 'static/vendor'
vendor.mkdir(parents=True, exist_ok=True)
assets = {
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css': 'bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js': 'bootstrap.bundle.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css': 'fontawesome/css/all.min.css',
}
base = root / 'templates/bo_cuc_chung.html'
text = base.read_text(encoding='utf-8')
text = '\n'.join(line for line in text.splitlines() if 'fonts.googleapis.com' not in line and 'fonts.gstatic.com' not in line)
text = text.replace("'Plus Jakarta Sans', sans-serif", "'Segoe UI', Arial, sans-serif")
base.write_text(text, encoding='utf-8')
paths = list((root / 'templates').rglob('*.html'))
for path in paths:
    text = path.read_text(encoding='utf-8')
    for url in re.findall(r'https://images\.unsplash\.com/[^\s\x22\x27)]+', text):
        if url not in assets:
            assets[url] = f'photo-{len(assets)}.jpg'
    for url, relative in assets.items():
        if url in text:
            destination = vendor / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                urllib.request.urlretrieve(url, destination)
            text = text.replace(url, '/static/vendor/' + relative)
    path.write_text(text, encoding='utf-8')
for font in ['fa-solid-900.woff2', 'fa-regular-400.woff2', 'fa-brands-400.woff2']:
    destination = vendor / 'fontawesome/webfonts' / font
    destination.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/' + font, destination)
print('All interface assets stored locally.')
