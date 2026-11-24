"""Tạo database mới, không xóa hoặc ghi đè dữ liệu cũ."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dhshop import settings
import MySQLdb

config = settings.DATABASES["default"]
name = config["NAME"]
if not name.replace("_", "").isalnum():
    raise ValueError("Tên database chỉ được gồm chữ, số và dấu gạch dưới.")
connection = MySQLdb.connect(
    host=config["HOST"],
    port=int(config["PORT"]),
    user=config["USER"],
    passwd=config["PASSWORD"],
    charset="utf8mb4",
    connect_timeout=5,
)
with connection.cursor() as cursor:
    cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
connection.close()
print(f"Database ready: {name}")
