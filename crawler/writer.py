import json
from pathlib import Path

from .config import ARCHIVE_DIR, ARCHIVE_FILENAME_FORMAT, PUBLIC_LATEST_DIR


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def write_latest(tab, filename, payload):
    target_dir = PUBLIC_LATEST_DIR / tab
    ensure_dir(target_dir)
    target = target_dir / filename
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_archive(tab, date_str, period, payload):
    year = date_str.split("-")[0]
    month = date_str.split("-")[1]
    archive_dir = ARCHIVE_DIR / tab / year / month
    ensure_dir(archive_dir)
    filename = ARCHIVE_FILENAME_FORMAT.format(date=date_str, period=period)
    target = archive_dir / filename
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
