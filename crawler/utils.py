import hashlib
import re
from datetime import datetime
from time import struct_time
from zoneinfo import ZoneInfo

from dateutil import parser


def parse_datetime(value, timezone):
    if not value:
        return None
    if isinstance(value, struct_time):
        dt = datetime(*value[:6], tzinfo=ZoneInfo(timezone))
        return dt.astimezone(ZoneInfo(timezone))
    try:
        dt = parser.parse(value)
    except (TypeError, ValueError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo(timezone))
    return dt.astimezone(ZoneInfo(timezone))


def make_hash(value):
    if value is None:
        value = ""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize_text(value):
    if not value:
        return ""
    return re.sub(r"\s+", " ", value.strip())


def format_date(dt):
    return dt.strftime("%Y-%m-%d")


def day_label(dt):
    return dt.strftime("%a")


def clamp_items(items, limit):
    return items[:limit]
