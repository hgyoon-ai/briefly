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
    TABS,
    TIMEZONE,
    WEEKLY_DAYS,
)
from crawler.fetchers.huggingface import fetch_huggingface_trending
from crawler.fetchers.hn import fetch_hacker_news_trending
from crawler.fetchers.rss import fetch_rss_sources
from crawler.llm.openai_client import summarize_item, summarize_issues
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
from crawler.run_stats import write_run_and_history


def load_items():
    timezone = TIMEZONE
    rss_items = fetch_rss_sources(RSS_SOURCES, timezone)
    hf_items = fetch_huggingface_trending(timezone)
    hn_items = fetch_hacker_news_trending(timezone)
    print(f"RSS items: {len(rss_items)}")
    print(f"Hugging Face models: {len(hf_items)}")
    print(f"Hacker News items: {len(hn_items)}")
    return rss_items + hf_items + hn_items


def count_by_source(items):
    counts = {}
    for item in items:
        name = item.get("source") or "Unknown"
        counts[name] = counts.get(name, 0) + 1
    return counts


def enrich_items(items):
    enriched = []
    for item in items:
        tab = item.get("tab", "ai")
        summary = summarize_item(item, tab=tab)
        enriched.append(
            {
                **item,
                "summary": summary["summary"],
                "why": summary["why"],
                "topics": summary["topics"],
                "status": summary["status"],
                "importanceScore": summary["importanceScore"],
            }
        )
    return enriched


def write_briefing_run_stats(payload):
    write_run_and_history(
        "public/briefing/run.json",
        "public/briefing/run_history.json",
        payload,
        limit=7,
    )


def clamp_total(items):
    if len(items) <= MAX_PER_SOURCE["total"]:
        return items
    return items[: MAX_PER_SOURCE["total"]]


def build_daily_payload(items, raw_count, now, tab="ai"):
    selected = select_diverse_by_source(items, max_total=5, max_per_source=2)
    daily = {
        "date": now.strftime("%Y-%m-%d"),
        "highlights": build_daily_summary(items, raw_count),
        "cards": build_cards(selected, tab=tab),
    }
    return daily


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


def select_diverse_by_source(items, max_total=5, max_per_source=2):
    selected = []
    counts = {}
    for item in items:
        source = item.get("source") or "Unknown"
        current = counts.get(source, 0)
        if current >= max_per_source:
            continue
        selected.append(item)
        counts[source] = current + 1
        if len(selected) >= max_total:
            break
    return selected


def iter_dates(start, end):
    current = start.date()
    end_date = end.date()
    while current <= end_date:
        yield current
        current += timedelta(days=1)


def load_archive_daily_items(start, end, timezone, tab):
    items = []
    for date in iter_dates(start, end):
        date_str = date.strftime("%Y-%m-%d")
        archive_path = (
            ARCHIVE_DIR
            / tab
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


def group_by_tab(items):
    grouped = {tab: [] for tab in TABS}
    for item in items:
        tab = item.get("tab", "ai")
        grouped.setdefault(tab, []).append(item)
    return grouped


def main():
    load_dotenv()
    timezone = ZoneInfo(TIMEZONE)
    now = datetime.now(timezone)

    errors = []
    run_stats = {
        "id": now.isoformat(),
        "ts": now.isoformat(),
        "timezone": TIMEZONE,
        "pipeline": {},
        "sources": {},
        "llm": {},
        "errors": errors,
    }

    try:
        raw_items = load_items()
        run_stats["pipeline"]["rawTotal"] = len(raw_items)

        run_stats["sources"] = {
            "rss": {
                "total": len([item for item in raw_items if item.get("kind") == "rss"]),
                "bySource": count_by_source([item for item in raw_items if item.get("kind") == "rss"]),
            },
            "hf": {
                "total": len([item for item in raw_items if item.get("kind") == "hf"]),
            },
            "hn": {
                "total": len([item for item in raw_items if item.get("kind") == "hn"]),
            },
        }

        raw_items = clamp_total(raw_items)
        run_stats["pipeline"]["rawClamped"] = len(raw_items)
        print(f"Total raw items (clamped): {len(raw_items)}")

        deduped = dedupe_items(raw_items)
        run_stats["pipeline"]["deduped"] = len(deduped)
        print(f"Deduped items: {len(deduped)}")

        # One summarize_item call per deduped item.
        run_stats["llm"]["itemCalls"] = len(deduped)

        enriched = enrich_items(deduped)
        run_stats["pipeline"]["enriched"] = len(enriched)
        print(f"Enriched items: {len(enriched)}")

        daily_start = now - timedelta(hours=DAILY_HOURS)
        weekly_start = now - timedelta(days=WEEKLY_DAYS - 1)
        monthly_start = now - timedelta(days=MONTHLY_DAYS - 1)

        today_str = now.strftime("%Y-%m-%d")
        raw_by_tab = group_by_tab(raw_items)
        enriched_by_tab = group_by_tab(enriched)

        run_stats["tabs"] = {}

        for tab in TABS:
            tab_items = enriched_by_tab.get(tab, [])
            daily_items = filter_by_range(tab_items, daily_start, now)
            daily_items = sort_by_importance(daily_items)
            raw_daily_count = len(filter_by_range(raw_by_tab.get(tab, []), daily_start, now))

            daily_payload = build_daily_payload(daily_items, raw_daily_count, now, tab=tab)
            write_latest(tab, "daily.json", daily_payload)
            write_archive(tab, today_str, "daily", daily_payload)

            archive_items = load_archive_daily_items(monthly_start, now, TIMEZONE, tab)
            weekly_items = filter_by_range(archive_items, weekly_start, now)
            monthly_items = filter_by_range(archive_items, monthly_start, now)
            weekly_items = sort_by_importance(weekly_items)
            monthly_items = sort_by_importance(monthly_items)
            print(f"[{tab}] Weekly items from archive: {len(weekly_items)}")
            print(f"[{tab}] Monthly items from archive: {len(monthly_items)}")

            weekly_issue_items = pick_diverse_items(weekly_items, max_items=8)
            monthly_issue_items = pick_diverse_items(monthly_items, max_items=8)

            # summarize_issues is called twice per tab.
            run_stats["llm"]["issueCalls"] = run_stats["llm"].get("issueCalls", 0) + 2
            weekly_issues = summarize_issues(weekly_issue_items, max_items=5, tab=tab)
            monthly_issues = summarize_issues(monthly_issue_items, max_items=5, tab=tab)

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

            write_latest(tab, "weekly.json", weekly_payload)
            write_latest(tab, "monthly.json", monthly_payload)
            write_archive(tab, today_str, "weekly", weekly_payload)
            write_archive(tab, today_str, "monthly", monthly_payload)

            run_stats["tabs"][tab] = {
                "daily": {"raw": raw_daily_count, "cards": len(daily_payload.get("cards") or [])},
                "weekly": {"items": len(weekly_items), "issues": len(weekly_issues or [])},
                "monthly": {"items": len(monthly_items), "issues": len(monthly_issues or [])},
            }

        print("Pipeline completed.")
    except Exception as exc:
        errors.append({"message": repr(exc)})
        raise
    finally:
        try:
            write_briefing_run_stats(run_stats)
        except Exception:
            # Best-effort: run stats must not break the pipeline.
            pass

if __name__ == "__main__":
    main()
