import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from crawler.config import ARCHIVE_DIR, ARCHIVE_FILENAME_FORMAT, TIMEZONE, WEEKLY_DAYS, MONTHLY_DAYS
from crawler.processor.aggregate import build_monthly_data, build_weekly_data, filter_by_range
from crawler.utils import parse_datetime
from crawler.writer import write_archive, write_latest


def iter_dates(start, end):
    current = start.date()
    end_date = end.date()
    while current <= end_date:
        yield current
        current += timedelta(days=1)


def load_archive_daily_items(start, end, timezone):
    items = []
    for date in iter_dates(start, end):
        date_str = date.strftime("%Y-%m-%d")
        archive_path = (
            ARCHIVE_DIR
            / date_str.split("-")[0]
            / date_str.split("-")[1]
            / ARCHIVE_FILENAME_FORMAT.format(date=date_str, period="daily")
        )
        if not archive_path.exists():
            continue
        payload = json.loads(archive_path.read_text(encoding="utf-8"))
        for card in payload.get("cards", []):
            published_at = parse_datetime(card.get("publishedAt"), timezone)
            if not published_at:
                continue
            items.append(
                {
                    "title": card.get("title"),
                    "url": card.get("url"),
                    "source": card.get("source"),
                    "published_at": published_at,
                    "summary": card.get("summary", []),
                    "why": card.get("whyItMatters"),
                    "topics": card.get("topics", []),
                    "status": card.get("status"),
                    "hash": card.get("hash"),
                    "tab": card.get("tab", "ai"),
                }
            )
    return items


def main():
    timezone = ZoneInfo(TIMEZONE)
    now = datetime.now(timezone)
    weekly_start = now - timedelta(days=WEEKLY_DAYS - 1)
    monthly_start = now - timedelta(days=MONTHLY_DAYS - 1)

    archive_items = load_archive_daily_items(monthly_start, now, TIMEZONE)
    weekly_items = filter_by_range(archive_items, weekly_start, now)
    monthly_items = filter_by_range(archive_items, monthly_start, now)

    print(f"Archive items loaded: {len(archive_items)}")
    print(f"Weekly items: {len(weekly_items)}")
    print(f"Monthly items: {len(monthly_items)}")

    weekly_payload = build_weekly_data(weekly_items, len(weekly_items), weekly_start, now)
    monthly_payload = build_monthly_data(monthly_items, len(monthly_items), monthly_start, now)

    write_latest("weekly.json", weekly_payload)
    write_latest("monthly.json", monthly_payload)

    today_str = now.strftime("%Y-%m-%d")
    write_archive(today_str, "weekly", weekly_payload)
    write_archive(today_str, "monthly", monthly_payload)

    print("Archive rollups completed.")


if __name__ == "__main__":
    main()
