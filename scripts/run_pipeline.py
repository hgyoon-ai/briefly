from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from crawler.config import (
    ARCHIVE_DIR,
    DAILY_HOURS,
    MAX_PER_SOURCE,
    MONTHLY_DAYS,
    RSS_SOURCES,
    TIMEZONE,
    WEEKLY_DAYS,
)
from crawler.fetchers.github import fetch_github_releases
from crawler.fetchers.huggingface import fetch_huggingface_trending
from crawler.fetchers.rss import fetch_rss_sources
from crawler.llm.groq_client import summarize_item
from crawler.processor.aggregate import (
    build_cards,
    build_daily_summary,
    build_monthly_data,
    build_weekly_data,
    filter_by_range,
)
from crawler.processor.dedupe import dedupe_items
from crawler.writer import write_archive, write_latest


def load_items():
    timezone = TIMEZONE
    items = []
    items.extend(fetch_rss_sources(RSS_SOURCES, timezone))
    items.extend(fetch_github_releases(timezone))
    items.extend(fetch_huggingface_trending(timezone))
    return items


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


def main():
    load_dotenv()
    timezone = ZoneInfo(TIMEZONE)
    now = datetime.now(timezone)

    raw_items = load_items()
    raw_items = clamp_total(raw_items)

    deduped = dedupe_items(raw_items)
    enriched = enrich_items(deduped)

    daily_start = now - timedelta(hours=DAILY_HOURS)
    weekly_start = now - timedelta(days=WEEKLY_DAYS - 1)
    monthly_start = now - timedelta(days=MONTHLY_DAYS - 1)

    daily_items = filter_by_range(enriched, daily_start, now)
    weekly_items = filter_by_range(enriched, weekly_start, now)
    monthly_items = filter_by_range(enriched, monthly_start, now)

    raw_daily_count = len(filter_by_range(raw_items, daily_start, now))
    raw_weekly_count = len(filter_by_range(raw_items, weekly_start, now))
    raw_monthly_count = len(filter_by_range(raw_items, monthly_start, now))

    daily_payload = build_daily_payload(daily_items, raw_daily_count, now)
    weekly_payload = build_weekly_data(weekly_items, raw_weekly_count, weekly_start, now)
    monthly_payload = build_monthly_data(monthly_items, raw_monthly_count, monthly_start, now)

    write_latest("daily.json", daily_payload)
    write_latest("weekly.json", weekly_payload)
    write_latest("monthly.json", monthly_payload)

    today_str = now.strftime("%Y-%m-%d")
    write_archive(today_str, "daily", daily_payload)
    write_archive(today_str, "weekly", weekly_payload)
    write_archive(today_str, "monthly", monthly_payload)

if __name__ == "__main__":
    main()
