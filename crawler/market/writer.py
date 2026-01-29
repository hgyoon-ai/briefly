import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path


def load_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def upsert_month_file(base_dir, month, events):
    month_path = Path(base_dir) / f"{month}.json"
    payload = load_json(month_path) or {"month": month, "events": []}
    existing = {item.get("id"): item for item in payload.get("events", []) if item.get("id")}
    for event in events:
        existing[event["id"]] = event
    merged = list(existing.values())
    merged.sort(key=lambda item: item.get("date") or "", reverse=True)
    payload["events"] = merged
    write_json(month_path, payload)
    return payload


def compute_quality(events):
    stats = {
        "total": len(events),
        "missingLink": 0,
        "missingSummary": 0,
        "missingType": 0,
        "missingArea": 0,
    }
    for event in events:
        if not event.get("sources") or not event["sources"][0].get("url"):
            stats["missingLink"] += 1
        if not event.get("oneLiner"):
            stats["missingSummary"] += 1
        if not (event.get("type") or event.get("type_raw")):
            stats["missingType"] += 1
        if not (event.get("areas") or event.get("areas_raw")):
            stats["missingArea"] += 1
    return stats


def build_index(base_dir, companies, now):
    base = Path(base_dir)
    months = []
    all_events = []
    quality_by_month = {}
    for path in sorted(base.glob("*.json")):
        payload = load_json(path)
        if not payload or "month" not in payload:
            continue
        months.append(payload["month"])
        events = payload.get("events", [])
        all_events.extend(events)
        quality_by_month[payload["month"]] = compute_quality(events)

    months = sorted(set(months), reverse=True)
    total_count = len(all_events)
    last30 = 0
    cutoff = (now - timedelta(days=30)).strftime("%Y-%m-%d")
    for event in all_events:
        if event.get("date") and event["date"] >= cutoff:
            last30 += 1

    last_updated = None
    if all_events:
        last_updated = max(item.get("date") or "" for item in all_events)

    return {
        "lastUpdated": last_updated,
        "months": months,
        "companies": companies,
        "counts": {"total": total_count, "last30d": last30},
        "qualityByMonth": quality_by_month,
    }
