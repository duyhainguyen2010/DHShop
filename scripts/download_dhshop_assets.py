"""Tải bộ ảnh mới của DHShop; lưu nguồn để dễ thay ảnh thật của cửa hàng."""

from pathlib import Path
import json
import urllib.request

root = Path(__file__).resolve().parent.parent
destination = root / "media/dhshop"
destination.mkdir(parents=True, exist_ok=True)
photos = {
    "campaign.jpg": (
        "photo-1496747611176-843222e1e57c",
        "Ảnh phong cách sống, dùng cho bộ sưu tập",
    ),
    "linen-shirt.jpg": ("photo-1596755094514-f87e34085b2c", "Áo sơ mi"),
    "cotton-tee.jpg": ("photo-1521572163474-6864f9cf17ab", "Áo thun trắng"),
    "polo.jpg": ("photo-1586790170083-2f9ceadc732d", "Áo polo"),
    "trousers.jpg": ("photo-1473966968600-fa801b869a1a", "Quần dài"),
    "denim.jpg": ("photo-1542272604-787c3835535d", "Quần denim"),
    "tailored.jpg": ("photo-1594633312681-425c7b97ccd1", "Quần nữ"),
    "dress.jpg": ("photo-1515372039744-b8f02a3ae446", "Váy"),
    "knitwear.jpg": ("photo-1434389677669-e08b4cac3105", "Áo dệt kim"),
}
sources = []
for filename, (photo_id, description) in photos.items():
    url = f"https://images.unsplash.com/{photo_id}?auto=format&fit=crop&w=1200&q=85"
    target = destination / filename
    if not target.exists():
        urllib.request.urlretrieve(url, target)
    sources.append(
        {
            "file": "media/dhshop/" + filename,
            "source": url,
            "description": description,
            "usage": "Ảnh minh họa cho đồ án, thay bằng ảnh thực tế khi kinh doanh.",
        }
    )
    print(filename)
(destination / "sources.json").write_text(
    json.dumps(sources, ensure_ascii=False, indent=2), encoding="utf-8"
)
