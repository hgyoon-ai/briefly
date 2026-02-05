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
from crawler.market.keywords import is_ai_candidate
from crawler.market.llm_batch import enrich_items, enrich_items_profile
from crawler.market.news_rss import build_items as build_news_items
from crawler.market.updates_keywords import is_updates_candidate
from crawler.market.taxonomy import (
    AREA_RAW_CHOICES,
    TYPE_RAW_CHOICES,
)
from crawler.market.writer import build_index, upsert_month_file, write_json
from crawler.utils import sha1_text
from crawler.run_stats import write_run_and_history


DEFAULT_DATASET = "all"
DATASET_CHOICES = ["all", "securities-ai", "securities-updates"]


def dataset_dirs(dataset):
    securities_dir = Path(f"public/securities/{dataset}")
    archive_dir = Path(f"archive/securities/{dataset}")
    return securities_dir, archive_dir


def load_index_companies(securities_dir):
    index_path = Path(securities_dir) / "index.json"
    if not index_path.exists():
        raise RuntimeError(f"index.json not found in {index_path}")
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    return payload.get("companies", [])


def load_cache(cache_path):
    cache_path = Path(cache_path)
    if not cache_path.exists():
        return {}
    cache = {}
    with cache_path.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            payload = json.loads(line)
            entry_id = payload.get("id")
            if entry_id:
                cache[entry_id] = payload
    return cache


def append_cache(items, cache_path, archive_dir):
    if not items:
        return
    archive_dir = Path(archive_dir)
    cache_path = Path(cache_path)
    archive_dir.mkdir(parents=True, exist_ok=True)
    with cache_path.open("a", encoding="utf-8") as file:
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
    pblntf_ty = entry.get("_pblntf_ty") or entry.get("pblntf_ty")
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
        # DART list.json includes `rm` (비고). Use it as a lightweight snippet for filtering.
        "snippet": entry.get("rm") or "",
        "date": date_str,
        "url": url,
        "source": "DART",
        "sourceType": "dart",
        "rcept_no": rcept_no,
        "pblntf_ty": pblntf_ty,
    }


def log_failure(failures_path, source_type, now, message, detail=None, company=None):
    payload = {
        "ts": now.strftime("%Y-%m-%dT%H:%M:%S"),
        "sourceType": source_type,
        "message": message,
    }
    if company:
        payload["company"] = company
    if detail:
        payload["detail"] = detail
    append_failure(failures_path, payload)


def write_unmatched(unmatched, archive_dir):
    if not unmatched:
        return
    path = Path(archive_dir) / "unmatched_companies.json"
    write_json(path, {"unmatched": unmatched})


def run_dataset(args, now, start, end, dataset, *, openai_key, dart_key):
    securities_dir, archive_dir = dataset_dirs(dataset)
    cache_path = archive_dir / "cache.jsonl"
    failures_path = archive_dir / "source_failures.jsonl"
    run_path = securities_dir / "run.json"
    run_history_path = securities_dir / "run_history.json"

    companies = load_index_companies(securities_dir)
    raw_items = []

    run_errors = []
    run_stats = {
        "id": now.isoformat(),
        "ts": now.isoformat(),
        "timezone": TIMEZONE,
        "dataset": dataset,
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
                failures_path,
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
            log_failure(failures_path, "app_store", now, "App Store fetch failed", detail=repr(exc))
            run_errors.append({"source": "app_store", "message": repr(exc)})

        run_stats["sources"]["app_store"] = {
            "appsTotal": len(APPSTORE_APPS),
            "fetchedOk": len(appstore_fetched),
            "failed": len(appstore_failed),
        }

        corp_map = {}
        dart_filters = {"pblntf_ty": ["B", "E", "I"], "last_reprt_at": "Y"}
        if dart_key:
            try:
                corp_map, unmatched = build_corp_code_map(companies, dart_key)
                write_unmatched(unmatched, archive_dir)
                run_stats["sources"]["dart"] = {
                    "companiesTotal": len(companies),
                    "matched": len(corp_map),
                    "unmatched": len(unmatched),
                    "filters": dart_filters,
                }
            except Exception as exc:
                log_failure(failures_path, "dart", now, "DART fetch failed", detail=repr(exc))
                run_errors.append({"source": "dart", "message": repr(exc)})
                corp_map = {}
        else:
            log_failure(failures_path, "dart", now, "DART_API_KEY not set; skipping DART")
            run_stats["sources"]["dart"] = {"skipped": True, "filters": dart_filters}

        for company, corp_code in corp_map.items():
            entries = list_disclosures(
                dart_key,
                corp_code,
                start,
                end,
                pblntf_ty=dart_filters["pblntf_ty"],
                last_reprt_at=dart_filters["last_reprt_at"],
            )
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
            log_failure(failures_path, "news", now, "News fetch failed", detail=repr(exc))
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
            if dataset == "securities-updates":
                # Always exclude AI-related items from the updates dataset.
                if is_ai_candidate(text):
                    continue

                # DART is an official channel; avoid over-filtering by update keywords.
                if source_type == "dart":
                    keyword_passed += 1
                    candidates.append(item)
                elif is_updates_candidate(text):
                    keyword_passed += 1
                    candidates.append(item)
                continue

            # securities-ai
            if is_ai_candidate(text):
                keyword_passed += 1
                candidates.append(item)

        run_stats["filters"]["keywordPassed"] = keyword_passed
        run_stats["filters"]["candidates"] = len(candidates)

        cache = load_cache(cache_path)
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
                log_failure(failures_path, "llm", now, "OPENAI_API_KEY not set; skipping enrichment")
                run_stats["llm"]["skippedNoKey"] = True
            else:
                try:
                    if dataset == "securities-updates":
                        enriched.update(
                            enrich_items_profile(
                                to_enrich,
                                "updates",
                                model=args.model,
                                batch_size=args.batch_size,
                            )
                        )
                    else:
                        enriched.update(
                            enrich_items(
                                to_enrich, model=args.model, batch_size=args.batch_size
                            )
                        )
                except Exception as exc:
                    log_failure(failures_path, "llm", now, "LLM enrichment failed", detail=repr(exc))
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

        append_cache(cache_updates, cache_path, archive_dir)

        events_by_month = {}
        for event in kept:
            month = to_month(event["date"])
            events_by_month.setdefault(month, []).append(event)

        for month, events in events_by_month.items():
            upsert_month_file(securities_dir, month, events)

        run_stats["output"] = {
            "kept": len(kept),
            "monthsUpdated": sorted(events_by_month.keys()),
        }

        index_payload = build_index(securities_dir, companies, now)
        write_json(Path(securities_dir) / "index.json", index_payload)

        print(f"Securities pipeline completed. Events kept: {len(kept)}")
    except Exception as exc:
        run_errors.append({"message": repr(exc)})
        raise
    finally:
        try:
            write_run_and_history(run_path, run_history_path, run_stats, limit=7)
        except Exception:
            pass


def main():
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, default=DEFAULT_DATASET, choices=DATASET_CHOICES)
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

    datasets = (
        ["securities-ai", "securities-updates"]
        if args.dataset == "all"
        else [args.dataset]
    )

    for dataset in datasets:
        run_dataset(
            args,
            now,
            start,
            end,
            dataset,
            openai_key=openai_key,
            dart_key=dart_key,
        )


if __name__ == "__main__":
    main()
