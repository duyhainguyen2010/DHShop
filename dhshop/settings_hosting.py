"""Cấu hình riêng cho SmarterASP.NET, dùng MySQL Connector/Python."""

import json
import os
from django.core.exceptions import ImproperlyConfigured

from .settings import *  # noqa: F403

# Trên SmarterASP, nhập JSON qua biến môi trường của Python App.
# Đường dẫn file dành cho kiểm tra cục bộ hoặc môi trường cho phép đọc file riêng.
config_json = os.environ.get("DHSHOP_CONFIG_JSON")
if config_json is None:
    config_path = Path(
        os.environ.get("DHSHOP_CONFIG_PATH", BASE_DIR.parent / "private" / "dhshop_config.json")
    )
    config_json = config_path.read_text(encoding="utf-8-sig")
config = json.loads(config_json)

SECRET_KEY = config["SECRET_KEY"]
if len(SECRET_KEY) < 50:
    raise ImproperlyConfigured("SECRET_KEY hosting phải có ít nhất 50 ký tự.")

DEBUG = False
ALLOWED_HOSTS = config["ALLOWED_HOSTS"]
CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS]
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
STATICFILES_DIRS = []

DATABASES = {
    "default": {
        "ENGINE": "mysql.connector.django",
        "NAME": config["DB_NAME"],
        "USER": config["DB_USER"],
        "PASSWORD": config["DB_PASSWORD"],
        "HOST": config["DB_HOST"],
        "PORT": config.get("DB_PORT", 3306),
        "CONN_MAX_AGE": 60,
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {
            "use_pure": True,
            "charset": "utf8mb4",
            "connection_timeout": 15,
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# WhiteNoise phục vụ CSS, JavaScript và font đã gom vào staticfiles.
MIDDLEWARE = [item for item in MIDDLEWARE if "WhiteNoise" not in item]
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
