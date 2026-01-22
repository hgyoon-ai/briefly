import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from crawler.config import (
    ARCHIVE_DIR,
    DAILY_HOURS,
    ARCHIVE_FILENAME_FORMAT,
    MAX_PER_SOURCE,
    MONTHLY_DAYS,
    RSS_SOURCES,
    TIMEZONE,
    WEEKLY_DAYS,
)
from crawler.fetchers.github import fetch_github_releases
from crawler.fetchers.huggingface import fetch_huggingface_trending
from crawler.fetchers.rss import fetch_rss_sources
from crawler.llm.gemini_client import summarize_item
from crawler.processor.aggregate import (
    build_cards,
    build_daily_summary,
    build_monthly_data,
    build_weekly_data,
    filter_by_range,
)
from crawler.processor.dedupe import dedupe_items
from crawler.utils import parse_datetime
from crawler.writer import write_archive, write_latest


def load_items():
    timezone = TIMEZONE
    rss_items = fetch_rss_sources(RSS_SOURCES, timezone)
    github_items = fetch_github_releases(timezone)
    hf_items = fetch_huggingface_trending(timezone)
    print(f"RSS items: {len(rss_items)}")
    print(f"GitHub releases: {len(github_items)}")
    print(f"Hugging Face models: {len(hf_items)}")
    return rss_items + github_items + hf_items


def enrich_items(items):
    enriched = []
    for item in items:
        summary = summarize_item(item)
        enriched.append(
            {
                **item,
                "summary": summary["summary"],
                "why": summary["why"],
                "topics": summary["topics"],
                "status": summary["status"],
            }
        )
    return enriched


def clamp_total(items):
    if len(items) <= MAX_PER_SOURCE["total"]:
        return items
    return items[: MAX_PER_SOURCE["total"]]


def build_daily_payload(items, raw_count, now):
    daily = {
        "date": now.strftime("%Y-%m-%d"),
        "highlights": build_daily_summary(items, raw_count),
        "cards": build_cards(items[:12]),
    }
    return daily


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
    load_dotenv()
    timezone = ZoneInfo(TIMEZONE)
    now = datetime.now(timezone)

    raw_items = load_items()
    raw_items = clamp_total(raw_items)
    print(f"Total raw items (clamped): {len(raw_items)}")

    deduped = dedupe_items(raw_items)
    print(f"Deduped items: {len(deduped)}")
    enriched = enrich_items(deduped)
    print(f"Enriched items: {len(enriched)}")

    daily_start = now - timedelta(hours=DAILY_HOURS)
    weekly_start = now - timedelta(days=WEEKLY_DAYS - 1)
    monthly_start = now - timedelta(days=MONTHLY_DAYS - 1)

    daily_items = filter_by_range(enriched, daily_start, now)
    raw_daily_count = len(filter_by_range(raw_items, daily_start, now))

    daily_payload = build_daily_payload(daily_items, raw_daily_count, now)
    write_latest("daily.json", daily_payload)

    today_str = now.strftime("%Y-%m-%d")
    write_archive(today_str, "daily", daily_payload)

    archive_items = load_archive_daily_items(monthly_start, now, TIMEZONE)
    weekly_items = filter_by_range(archive_items, weekly_start, now)
    monthly_items = filter_by_range(archive_items, monthly_start, now)
    print(f"Weekly items from archive: {len(weekly_items)}")
    print(f"Monthly items from archive: {len(monthly_items)}")

    weekly_payload = build_weekly_data(weekly_items, len(weekly_items), weekly_start, now)
    monthly_payload = build_monthly_data(monthly_items, len(monthly_items), monthly_start, now)

    write_latest("weekly.json", weekly_payload)
    write_latest("monthly.json", monthly_payload)
    write_archive(today_str, "weekly", weekly_payload)
    write_archive(today_str, "monthly", monthly_payload)

    print("Pipeline completed.")

if __name__ == "__main__":
    main()
