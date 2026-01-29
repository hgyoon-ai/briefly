import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

from crawler.config import TIMEZONE
from crawler.market.appstore import build_items as build_appstore_items
from crawler.market.appstore_apps import APPS as APPSTORE_APPS
from crawler.market.dart import (
    build_corp_code_map,
    build_disclosure_url,
    list_disclosures,
    parse_rcept_date,
)
from crawler.market.failures import append_failure
from crawler.market.keywords import is_ai_candidate, is_soft_candidate
from crawler.market.llm_batch import enrich_items
from crawler.market.news_rss import build_items as build_news_items
from crawler.market.taxonomy import (
    AREA_RAW_CHOICES,
    TYPE_RAW_CHOICES,
)
from crawler.market.writer import build_index, upsert_month_file, write_json
from crawler.utils import sha1_text
from crawler.run_stats import write_run_and_history


MARKET_DIR = Path("public/market/securities-ai")
ARCHIVE_DIR = Path("archive/market/securities-ai")
CACHE_PATH = ARCHIVE_DIR / "cache.jsonl"
FAILURES_PATH = ARCHIVE_DIR / "source_failures.jsonl"

RUN_PATH = MARKET_DIR / "run.json"
RUN_HISTORY_PATH = MARKET_DIR / "run_history.json"


def load_index_companies():
    index_path = MARKET_DIR / "index.json"
    if not index_path.exists():
        raise RuntimeError("index.json not found in public/market/securities-ai")
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    return payload.get("companies", [])


def load_cache():
    if not CACHE_PATH.exists():
        return {}
    cache = {}
    with CACHE_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            payload = json.loads(line)
            entry_id = payload.get("id")
            if entry_id:
                cache[entry_id] = payload
    return cache


def append_cache(items):
    if not items:
        return
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    with CACHE_PATH.open("a", encoding="utf-8") as file:
        for item in items:
            file.write(json.dumps(item, ensure_ascii=False) + "\n")


def to_month(date_str):
    return date_str[:7]


def get_time_range(args, now):
    if args.month:
        start = datetime.strptime(args.month, "%Y-%m")
        next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        end = next_month - timedelta(seconds=1)
        return start, end
    end = now
    start = end - timedelta(days=args.lookback_days)
    return start, end


def build_item(company, corp_code, entry):
    rcept_no = entry.get("rcept_no")
    report_nm = entry.get("report_nm")
    rcept_dt = entry.get("rcept_dt")
    date_obj = parse_rcept_date(rcept_dt)
    date_str = date_obj.strftime("%Y-%m-%d") if date_obj else None
    url = build_disclosure_url(rcept_no)
    item_id = sha1_text(
        f"{company}-{rcept_no}" if rcept_no else f"{company}-{report_nm}-{date_str}"
    )
    return {
        "id": item_id,
        "company": company,
        "corp_code": corp_code,
        "title": report_nm,
        "snippet": "",
        "date": date_str,
        "url": url,
        "source": "DART",
        "sourceType": "dart",
        "rcept_no": rcept_no,
    }


def log_failure(source_type, now, message, detail=None, company=None):
    payload = {
        "ts": now.strftime("%Y-%m-%dT%H:%M:%S"),
        "sourceType": source_type,
        "message": message,
    }
    if company:
        payload["company"] = company
    if detail:
        payload["detail"] = detail
    append_failure(FAILURES_PATH, payload)


def write_unmatched(unmatched):
    if not unmatched:
        return
    path = ARCHIVE_DIR / "unmatched_companies.json"
    write_json(path, {"unmatched": unmatched})


def main():
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--lookback-days", type=int, default=3)
    parser.add_argument("--month", type=str, default=None)
    parser.add_argument("--model", type=str, default="gpt-5-mini")
    parser.add_argument("--batch-size", type=int, default=12)
    args = parser.parse_args()

    import os

    dart_key = os.getenv("DART_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    from zoneinfo import ZoneInfo

    now = datetime.now(ZoneInfo(TIMEZONE))
    start, end = get_time_range(args, now)
    if start.tzinfo is None:
        start = start.replace(tzinfo=ZoneInfo(TIMEZONE))
    if end.tzinfo is None:
        end = end.replace(tzinfo=ZoneInfo(TIMEZONE))

    companies = load_index_companies()
    raw_items = []

    run_errors = []
    run_stats = {
        "id": now.isoformat(),
        "ts": now.isoformat(),
        "timezone": TIMEZONE,
        "range": {
            "mode": "month" if args.month else "lookback",
            "lookbackDays": args.lookback_days,
            "month": args.month,
            "start": start.isoformat(),
            "end": end.isoformat(),
        },
        "sources": {},
        "filters": {},
        "llm": {},
        "output": {},
        "errors": run_errors,
    }

    try:
        appstore_failed = []
        appstore_fetched = set()

        def on_appstore_failure(company, track_id, exc):
            appstore_failed.append(
                {"company": company, "trackId": track_id, "error": repr(exc)}
            )
            log_failure(
                "app_store",
                now,
                "App Store fetch failed",
                detail=f"trackId={track_id} err={repr(exc)}",
                company=company,
            )

        def on_appstore_fetched(company, track_id):
            appstore_fetched.add(str(track_id))

        try:
            appstore_items = build_appstore_items(
                APPSTORE_APPS,
                start,
                end,
                now,
                on_failure=on_appstore_failure,
                on_fetched=on_appstore_fetched,
            )
            raw_items.extend(appstore_items)
        except Exception as exc:
            log_failure("app_store", now, "App Store fetch failed", detail=repr(exc))
            run_errors.append({"source": "app_store", "message": repr(exc)})

        run_stats["sources"]["app_store"] = {
            "appsTotal": len(APPSTORE_APPS),
            "fetchedOk": len(appstore_fetched),
            "failed": len(appstore_failed),
        }

        corp_map = {}
        if dart_key:
            try:
                corp_map, unmatched = build_corp_code_map(companies, dart_key)
                write_unmatched(unmatched)
                run_stats["sources"]["dart"] = {
                    "companiesTotal": len(companies),
                    "matched": len(corp_map),
                    "unmatched": len(unmatched),
                }
            except Exception as exc:
                log_failure("dart", now, "DART fetch failed", detail=repr(exc))
                run_errors.append({"source": "dart", "message": repr(exc)})
                corp_map = {}
        else:
            log_failure("dart", now, "DART_API_KEY not set; skipping DART")
            run_stats["sources"]["dart"] = {"skipped": True}

        for company, corp_code in corp_map.items():
            entries = list_disclosures(dart_key, corp_code, start, end)
            for entry in entries:
                item = build_item(company, corp_code, entry)
                if not item.get("date"):
                    continue
                raw_items.append(item)

        if "dart" in run_stats.get("sources", {}):
            run_stats["sources"]["dart"]["disclosuresFetched"] = len(
                [item for item in raw_items if item.get("sourceType") == "dart"]
            )

        try:
            news_items, news_meta = build_news_items(companies, start, end)
            raw_items.extend(news_items)
            run_stats["sources"]["news"] = {"rssLimit": 50, **news_meta}
        except Exception as exc:
            log_failure("news", now, "News fetch failed", detail=repr(exc))
            run_errors.append({"source": "news", "message": repr(exc)})

        seen = {}
        for item in raw_items:
            seen[item["id"]] = item
        deduped = list(seen.values())

        run_stats["filters"]["rawItems"] = len(raw_items)
        run_stats["filters"]["deduped"] = len(deduped)

        candidates = []
        keyword_passed = 0
        for item in deduped:
            title = item.get("title") or ""
            snippet = item.get("snippet") or ""
            text = f"{title} {snippet}".strip()
            source_type = item.get("sourceType")
            if source_type in ("app_store", "news"):
                if is_ai_candidate(text):
                    keyword_passed += 1
                    candidates.append(item)
                continue
            if is_ai_candidate(text) or is_soft_candidate(text):
                keyword_passed += 1
                candidates.append(item)

        run_stats["filters"]["keywordPassed"] = keyword_passed
        run_stats["filters"]["candidates"] = len(candidates)

        cache = load_cache()
        to_enrich = []
        enriched = {}
        cache_hit = 0
        for item in candidates:
            cached = cache.get(item["id"])
            if cached:
                cache_hit += 1
                enriched[item["id"]] = cached
            else:
                to_enrich.append(
                    {
                        "id": item["id"],
                        "company": item["company"],
                        "title": item["title"],
                        "snippet": item.get("snippet") or "",
                        "source": item["source"],
                        "date": item["date"],
                        "url": item["url"],
                    }
                )

        if to_enrich:
            if not openai_key:
                log_failure("llm", now, "OPENAI_API_KEY not set; skipping enrichment")
                run_stats["llm"]["skippedNoKey"] = True
            else:
                try:
                    enriched.update(
                        enrich_items(to_enrich, model=args.model, batch_size=args.batch_size)
                    )
                except Exception as exc:
                    log_failure("llm", now, "LLM enrichment failed", detail=repr(exc))
                    run_errors.append({"source": "llm", "message": repr(exc)})

        run_stats["llm"].update(
            {
                "cacheHit": cache_hit,
                "sent": len(to_enrich) if openai_key else 0,
            }
        )

        cache_updates = []
        kept = []
        for item in candidates:
            result = enriched.get(item["id"])
            if not result:
                continue
            keep = result.get("keep") is True
            if not keep:
                cache_updates.append({"id": item["id"], **result})
                continue
            type_raw = result.get("type_raw")
            if type_raw not in TYPE_RAW_CHOICES:
                type_raw = "기타"
            areas_raw = [
                item
                for item in (result.get("areas_raw") or [])
                if item in AREA_RAW_CHOICES
            ]
            if not areas_raw:
                areas_raw = ["기타"]
            kept.append(
                {
                    "id": item["id"],
                    "date": item["date"],
                    "company": item["company"],
                    "title": item["title"],
                    "oneLiner": result.get("oneLiner") or "",
                    "type": type_raw,
                    "areas": areas_raw,
                    "region": "국내",
                    "sourceType": item.get("sourceType") or "dart",
                    "sources": [
                        {
                            "source": item["source"],
                            "title": item["title"],
                            "url": item["url"],
                        }
                    ],
                    "tags": [],
                    "confidence": result.get("confidence"),
                    "updatedAt": now.strftime("%Y-%m-%d"),
                }
            )
            cache_updates.append({"id": item["id"], **result})

        append_cache(cache_updates)

        events_by_month = {}
        for event in kept:
            month = to_month(event["date"])
            events_by_month.setdefault(month, []).append(event)

        for month, events in events_by_month.items():
            upsert_month_file(MARKET_DIR, month, events)

        run_stats["output"] = {
            "kept": len(kept),
            "monthsUpdated": sorted(events_by_month.keys()),
        }

        index_payload = build_index(MARKET_DIR, companies, now)
        write_json(MARKET_DIR / "index.json", index_payload)

        print(f"Market pipeline completed. Events kept: {len(kept)}")
    except Exception as exc:
        run_errors.append({"message": repr(exc)})
        raise
    finally:
        try:
            write_run_and_history(RUN_PATH, RUN_HISTORY_PATH, run_stats, limit=7)
        except Exception:
            pass


if __name__ == "__main__":
    main()
