"""Kiểm tra backend MySQL hosting bằng database cục bộ."""

import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / "runtime/hosting-common"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dhshop.settings")

import django
from dhshop import settings
from django.core.management import call_command

settings.DATABASES["default"]["ENGINE"] = "mysql.connector.django"
settings.DATABASES["default"]["OPTIONS"]["use_pure"] = True
django.setup()
call_command("test", "cua_hang", "gio_hang", "khach_hang", verbosity=1, interactive=False)
