"""Thử nạp SQL vào database mới và kiểm tra website với cấu hình hosting."""

import json
import os
import secrets
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
from dhshop import settings as local
import MySQLdb

db = local.DATABASES["default"]
name = "tmp_dhshop_hosting_" + secrets.token_hex(4)
connection = MySQLdb.connect(host=db["HOST"], port=int(db["PORT"]),
                             user=db["USER"], passwd=db["PASSWORD"], charset="utf8mb4")
created = False
try:
    with connection.cursor() as cursor:
        cursor.execute(f"CREATE DATABASE `{name}` CHARACTER SET utf8mb4")
        created = True
    environment = os.environ.copy()
    environment["MYSQL_PWD"] = db["PASSWORD"]
    with (root / "hosting-output/private/dhshop_mysql.sql").open("rb") as stream:
        subprocess.run([
            "C:/wamp64/bin/mysql/mysql8.4.7/bin/mysql.exe", "--no-defaults",
            "--host=" + db["HOST"], "--port=" + db["PORT"], "--user=" + db["USER"],
            "--default-character-set=utf8mb4", name,
        ], stdin=stream, env=environment, check=True)

    config = json.loads((root / "hosting-output/private/dhshop_config.json").read_text())
    config.update(DB_NAME=name, DB_HOST=db["HOST"], DB_PORT=int(db["PORT"]),
                  DB_USER=db["USER"], DB_PASSWORD=db["PASSWORD"])
    target = root / "runtime/hosting-check-config.json"
    target.write_text(json.dumps(config), encoding="utf-8")
    os.environ["DHSHOP_CONFIG_PATH"] = str(target)
    os.environ["DJANGO_SETTINGS_MODULE"] = "dhshop.settings_hosting"
    sys.path.insert(0, str(root / "runtime/hosting-common"))
    import django
    django.setup()
    from django.test import Client
    from django.contrib.auth import authenticate
    from cua_hang.models import SanPham
    from django.contrib.auth.models import User
    from django.db import connections
    from django.core.management import call_command
    call_command("check", verbosity=0)
    client = Client(HTTP_HOST=config["ALLOWED_HOSTS"][0])
    assert client.get("/", secure=True).status_code == 200
    assert client.get("/static/css/base.css", secure=True).status_code == 200
    assert client.get("/media/dhshop/linen-shirt.jpg", secure=True).status_code == 200
    credentials = json.loads((root / "hosting-output/private/admin.json").read_text())
    assert authenticate(email=credentials["email"], password=credentials["password"]).is_superuser
    assert User.objects.count() == 1
    assert SanPham.objects.count() == 8
    print("PASS: SQL import, catalog, admin login, homepage, CSS and media (DEBUG=False).")
    connections.close_all()
finally:
    if created and name.startswith("tmp_dhshop_hosting_"):
        with connection.cursor() as cursor:
            cursor.execute(f"DROP DATABASE `{name}`")
    connection.close()
