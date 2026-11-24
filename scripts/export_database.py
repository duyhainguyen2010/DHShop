"""Xuất schema và dữ liệu demo MySQL để mang theo khi nộp."""

from pathlib import Path
import os
import subprocess
import sys

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
from dhshop import settings

config = settings.DATABASES["default"]
dump_path = (
    Path(sys.argv[1])
    if len(sys.argv) > 1
    else Path("C:/wamp64/bin/mysql/mysql8.4.7/bin/mysqldump.exe")
)
environment = os.environ.copy()
environment["MYSQL_PWD"] = config["PASSWORD"]
target = root / "docs/dhshop_demo.sql"
with target.open("wb") as output:
    subprocess.run(
        [
            str(dump_path),
            "--no-defaults",
            "--host=" + config["HOST"],
            "--port=" + config["PORT"],
            "--user=" + config["USER"],
            "--single-transaction",
            "--set-gtid-purged=OFF",
            "--no-tablespaces",
            "--default-character-set=utf8mb4",
            config["NAME"],
        ],
        stdout=output,
        env=environment,
        check=True,
    )
print("Database dump created: docs/dhshop_demo.sql")
