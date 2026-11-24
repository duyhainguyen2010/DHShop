"""Lưu font Lora có hỗ trợ tiếng Việt và giấy phép OFL để dùng offline."""

from pathlib import Path
import urllib.request

font_directory = Path(__file__).resolve().parent.parent / "static/fonts/lora"
font_directory.mkdir(parents=True, exist_ok=True)

files = {
    "Lora-Regular.ttf": "Lora%5Bwght%5D.ttf",
    "Lora-Italic.ttf": "Lora-Italic%5Bwght%5D.ttf",
    "OFL.txt": "OFL.txt",
}

for filename, remote_filename in files.items():
    source = "https://raw.githubusercontent.com/google/fonts/main/ofl/lora/" + remote_filename
    urllib.request.urlretrieve(source, font_directory / filename)
    print(filename)
