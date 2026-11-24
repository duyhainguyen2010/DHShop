"""Tạo ZIP Linux Python 3.14 và SQL riêng, không xuất tài khoản/đơn hàng cục bộ."""

import json
import os
import secrets
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dhshop.settings")

import django
django.setup()

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.management import call_command
from django.core.validators import validate_email
from django.db import connection

output = root / "hosting-output"
private = output / "private"
private.mkdir(parents=True, exist_ok=True)

# Giữ nguyên thông tin quản trị khi đóng gói lại; không đổi mật khẩu mỗi lần build.
credentials_path = private / "admin.json"
if credentials_path.exists():
    credentials = json.loads(credentials_path.read_text(encoding="utf-8"))
else:
    credentials = {"username": "dhadmin", "email": "", "password": secrets.token_urlsafe(20)}
    credentials_path.write_text(json.dumps(credentials, indent=2), encoding="utf-8")

admin_email = credentials.get("email", "").strip().lower()
if not admin_email:
    raise SystemExit("Điền email quản trị vào hosting-output/private/admin.json trước khi đóng gói.")
validate_email(admin_email)

config_path = private / "dhshop_config.json"
if not config_path.exists():
    config = {
        "SECRET_KEY": secrets.token_urlsafe(64),
        "ALLOWED_HOSTS": ["dhshop2026-002-site1.ltempurl.com"],
        "DB_NAME": "db_ad12f0_dhshop",
        "DB_USER": "ad12f0_dhshop",
        "DB_HOST": "mysql5045.site4now.net",
        "DB_PORT": 3306,
        "DB_PASSWORD": "DIEN_MAT_KHAU_DATABASE",
    }
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

call_command("collectstatic", interactive=False, verbosity=0)

# Xuất schema, quyền Django và danh mục; không mang sessions, khách hàng hay đơn cũ.
db = settings.DATABASES["default"]
environment = os.environ.copy()
environment["MYSQL_PWD"] = db["PASSWORD"]
dump = "C:/wamp64/bin/mysql/mysql8.4.7/bin/mysqldump.exe"
arguments = [
    dump, "--no-defaults", "--host=" + db["HOST"], "--port=" + db["PORT"],
    "--user=" + db["USER"], "--single-transaction", "--set-gtid-purged=OFF",
    "--no-tablespaces", "--default-character-set=utf8mb4", "--skip-comments",
    "--skip-add-locks", "--skip-add-drop-table",
]
sql_path = private / "dhshop_mysql.sql"
with sql_path.open("wb") as stream:
    subprocess.run(arguments + ["--no-data", db["NAME"]], stdout=stream, env=environment, check=True)
    tables = [
        "django_migrations", "django_content_type", "auth_permission",
        "cua_hang_danhmuc", "cua_hang_sanpham", "cua_hang_anhsanpham",
    ]
    subprocess.run(arguments + ["--no-create-info", db["NAME"]] + tables,
                   stdout=stream, env=environment, check=True)

connection.ensure_connection()
def literal(value):
    result = connection.connection.literal(value)
    return result.decode("utf-8") if isinstance(result, bytes) else result

now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
with sql_path.open("a", encoding="utf-8") as stream:
    stream.write("\nINSERT INTO auth_user "
                 "(id,password,last_login,is_superuser,username,first_name,last_name,email,is_staff,is_active,date_joined) "
                 f"VALUES (1,{literal(make_password(credentials['password']))},NULL,1,"
                 f"{literal(credentials['username'])},'','',{literal(admin_email)},1,1,{literal(now)});\n")
    stream.write("INSERT INTO khach_hang_hosokhachhang "
                 "(user_id,so_dien_thoai,dia_chi,ngay_tao) "
                 f"VALUES (1,'','',{literal(now)});\n")

archive_path = output / "DHShop_Linux_Python314.zip"
folders = ["cua_hang", "gio_hang", "khach_hang", "dhshop", "templates", "staticfiles", "media"]
with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
    for folder in folders:
        for path in sorted((root / folder).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                archive.write(path, path.relative_to(root))
    for source in [root / "runtime/hosting-common", root / "runtime/hosting-pillow"]:
        if not source.is_dir():
            raise RuntimeError(f"Chưa chuẩn bị thư viện: {source.name}")
        for path in sorted(source.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                archive.write(path, Path("_vendor") / path.relative_to(source))
    archive.write(root / "hosting_wsgi.py", "hosting_wsgi.py")

with zipfile.ZipFile(archive_path) as archive:
    assert archive.testzip() is None
    assert "hosting_wsgi.py" in archive.namelist()
    assert not any(name.endswith((".sql", "dhshop_config.json", ".env", "admin.json"))
                   for name in archive.namelist())

print(f"Hosting ZIP: {archive_path} ({archive_path.stat().st_size:,} bytes)")
print("Private configuration, SQL and administrator credentials: hosting-output/private")
