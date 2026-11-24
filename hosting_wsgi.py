"""Điểm khởi động Django trên hosting đã có sẵn thư viện trong _vendor."""

import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "_vendor"))
os.environ["DJANGO_SETTINGS_MODULE"] = "dhshop.settings_hosting"


def write_startup_log(message):
    """Lưu log ngoài thư mục web; không ghi mật khẩu, cookie hay cấu hình đầy đủ."""
    line = f"{datetime.now(timezone.utc).isoformat()} {message}\n"
    try:
        log_path = project_root.parent / "private" / "dhshop_startup.log"
        with log_path.open("a", encoding="utf-8") as stream:
            stream.write(line)
    except OSError:
        # Hosting vẫn có thể thu thập stderr nếu không cấp quyền ghi file riêng.
        print(line, file=sys.stderr, flush=True)


try:
    write_startup_log(f"Starting Python {sys.version.split()[0]}, root={project_root}")
    from django.core.wsgi import get_wsgi_application

    django_application = get_wsgi_application()
    write_startup_log("Django WSGI initialized")
except Exception:
    write_startup_log(traceback.format_exc())
    raise


def application(environ, start_response):
    """Ghi trạng thái lỗi để chẩn đoán health check, không thay đổi phản hồi Django."""
    def record_response(status, headers, exc_info=None):
        if int(status.split()[0]) >= 400:
            write_startup_log(
                f"HTTP {status}; host={environ.get('HTTP_HOST', '')!r}; "
                f"path={environ.get('PATH_INFO', '')!r}"
            )
        return start_response(status, headers, exc_info)

    return django_application(environ, record_response)
