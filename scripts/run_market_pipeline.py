import argparse
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

from crawler.config import TIMEZONE
from crawler.market.dart import (
    build_corp_code_map,
    build_disclosure_url,
    list_disclosures,
    parse_rcept_date,
)
from crawler.market.keywords import is_ai_candidate, is_soft_candidate
from crawler.market.llm_batch import enrich_items
from crawler.market.taxonomy import (
    AREA_RAW_CHOICES,
    TYPE_RAW_CHOICES,
    map_area_groups,
    map_type_group,
)
from crawler.market.writer import build_index, upsert_month_file, write_json


MARKET_DIR = Path("public/market/securities-ai")
ARCHIVE_DIR = Path("archive/market/securities-ai")
CACHE_PATH = ARCHIVE_DIR / "cache.jsonl"


def sha1(value):
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


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
    for line in CACHE_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        cache[payload["id"]] = payload
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
        end = start.replace(day=28) + timedelta(days=4)
        end = end.replace(day=1) - timedelta(days=1)
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
    item_id = sha1(f"{company}-{rcept_no}" if rcept_no else f"{company}-{report_nm}-{date_str}")
    return {
        "id": item_id,
        "company": company,
        "corp_code": corp_code,
        "title": report_nm,
        "date": date_str,
        "url": url,
        "source": "DART",
        "rcept_no": rcept_no,
    }


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
    if not dart_key:
        raise RuntimeError("DART_API_KEY not set")

    from zoneinfo import ZoneInfo

    now = datetime.now(ZoneInfo(TIMEZONE))
    start, end = get_time_range(args, now)

    companies = load_index_companies()
    corp_map, unmatched = build_corp_code_map(companies, dart_key)
    write_unmatched(unmatched)

    raw_items = []
    for company, corp_code in corp_map.items():
        entries = list_disclosures(dart_key, corp_code, start, end)
        for entry in entries:
            item = build_item(company, corp_code, entry)
            if not item.get("date"):
                continue
            raw_items.append(item)

    seen = {}
    for item in raw_items:
        seen[item["id"]] = item
    deduped = list(seen.values())

    candidates = []
    for item in deduped:
        title = item.get("title") or ""
        if is_ai_candidate(title) or is_soft_candidate(title):
            candidates.append(item)

    cache = load_cache()
    to_enrich = []
    enriched = {}
    for item in candidates:
        cached = cache.get(item["id"])
        if cached:
            enriched[item["id"]] = cached
        else:
            to_enrich.append(
                {
                    "id": item["id"],
                    "company": item["company"],
                    "title": item["title"],
                    "snippet": "",
                    "source": item["source"],
                    "date": item["date"],
                    "url": item["url"],
                }
            )

    if to_enrich:
        enriched.update(enrich_items(to_enrich, model=args.model, batch_size=args.batch_size))

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
        areas_raw = [item for item in (result.get("areas_raw") or []) if item in AREA_RAW_CHOICES]
        if not areas_raw:
            areas_raw = ["기타"]
        type_group = map_type_group(type_raw)
        areas_group = map_area_groups(areas_raw)
        kept.append(
            {
                "id": item["id"],
                "date": item["date"],
                "company": item["company"],
                "title": item["title"],
                "oneLiner": result.get("oneLiner") or "",
                "type_raw": type_raw,
                "areas_raw": areas_raw,
                "type_group": type_group,
                "areas_group": areas_group,
                "sources": [
                    {
                        "source": item["source"],
                        "title": item["title"],
                        "url": item["url"],
                    }
                ],
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

    index_payload = build_index(MARKET_DIR, companies, now)
    write_json(MARKET_DIR / "index.json", index_payload)

    print(f"Market pipeline completed. Events kept: {len(kept)}")


if __name__ == "__main__":
    main()
