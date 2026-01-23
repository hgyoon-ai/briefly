import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from crawler.config import ARCHIVE_DIR, ARCHIVE_FILENAME_FORMAT, TIMEZONE, WEEKLY_DAYS, MONTHLY_DAYS
from crawler.processor.aggregate import build_monthly_data, build_weekly_data, filter_by_range
from crawler.utils import parse_datetime
from crawler.writer import write_archive, write_latest
from crawler.llm.openai_client import summarize_issues


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
                    "importanceScore": card.get("importanceScore"),
                    "tab": card.get("tab", "ai"),
                }
            )
    return items


def sort_by_importance(items):
    return sorted(
        items,
        key=lambda item: (
            item.get("importanceScore") or 0,
            item.get("published_at") or datetime.min,
        ),
        reverse=True,
    )


def pick_diverse_items(items, max_items=8):
    selected = []
    used_topics = set()
    for item in items:
        topics = item.get("topics") or []
        primary = topics[0] if topics else None
        if primary and primary in used_topics:
            continue
        if primary:
            used_topics.add(primary)
        selected.append(item)
        if len(selected) >= max_items:
            return selected
    for item in items:
        if item in selected:
            continue
        selected.append(item)
        if len(selected) >= max_items:
            break
    return selected


def main():
    load_dotenv()
    timezone = ZoneInfo(TIMEZONE)
    now = datetime.now(timezone)
    weekly_start = now - timedelta(days=WEEKLY_DAYS - 1)
    monthly_start = now - timedelta(days=MONTHLY_DAYS - 1)

    archive_items = load_archive_daily_items(monthly_start, now, TIMEZONE)
    weekly_items = filter_by_range(archive_items, weekly_start, now)
    monthly_items = filter_by_range(archive_items, monthly_start, now)
    weekly_items = sort_by_importance(weekly_items)
    monthly_items = sort_by_importance(monthly_items)

    print(f"Archive items loaded: {len(archive_items)}")
    print(f"Weekly items: {len(weekly_items)}")
    print(f"Monthly items: {len(monthly_items)}")

    weekly_issue_items = pick_diverse_items(weekly_items, max_items=8)
    monthly_issue_items = pick_diverse_items(monthly_items, max_items=8)
    weekly_issues = summarize_issues(weekly_issue_items, max_items=5)
    monthly_issues = summarize_issues(monthly_issue_items, max_items=5)

    weekly_payload = build_weekly_data(
        weekly_items,
        len(weekly_items),
        weekly_start,
        now,
        issues=weekly_issues,
    )
    monthly_payload = build_monthly_data(
        monthly_items,
        len(monthly_items),
        monthly_start,
        now,
        issues=monthly_issues,
    )

    write_latest("weekly.json", weekly_payload)
    write_latest("monthly.json", monthly_payload)

    today_str = now.strftime("%Y-%m-%d")
    write_archive(today_str, "weekly", weekly_payload)
    write_archive(today_str, "monthly", monthly_payload)

    print("Archive rollups completed.")


if __name__ == "__main__":
    main()
