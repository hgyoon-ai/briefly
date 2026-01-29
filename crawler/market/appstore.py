import hashlib

import requests

from crawler.config import TIMEZONE
from crawler.utils import format_date, normalize_text, parse_datetime


LOOKUP_URL = "https://itunes.apple.com/lookup"


def sha1(value):
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def fetch_app(track_id, country="kr"):
    response = requests.get(
        LOOKUP_URL,
        params={"id": str(track_id), "country": country},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    results = payload.get("results") or []
    if not results:
        raise RuntimeError(f"App Store lookup returned 0 results: trackId={track_id}")
    return results[0]


def _in_range(dt, start, end):
    if not dt:
        return False
    if start and dt < start:
        return False
    if end and dt > end:
        return False
    return True


def build_items(apps, start, end, now, country="kr"):
    items = []
    for app in apps:
        track_id = app.get("trackId")
        company = app.get("company")
        if not track_id or not company:
            continue

        entry = fetch_app(track_id, country=country)
        version = normalize_text(entry.get("version"))
        release_date = entry.get("currentVersionReleaseDate")
        dt = parse_datetime(release_date, TIMEZONE)
        if not _in_range(dt, start, end):
            continue

        track_name = normalize_text(entry.get("trackName")) or normalize_text(app.get("appName"))
        url = entry.get("trackViewUrl")
        notes = normalize_text(entry.get("releaseNotes"))

        date_str = format_date(dt) if dt else None
        if not date_str:
            continue

        item_id = sha1(f"{company}-appstore-{track_id}-{version}-{date_str}")
        title = f"{company} iOS 앱 업데이트 v{version}" if version else f"{company} iOS 앱 업데이트"
        snippet = notes[:1000]
        items.append(
            {
                "id": item_id,
                "company": company,
                "title": title,
                "snippet": snippet,
                "source": "App Store",
                "sourceType": "app_store",
                "date": date_str,
                "url": url,
                "trackId": track_id,
                "appName": track_name,
                "version": version,
                "currentVersionReleaseDate": release_date,
                "fetchedAt": now.strftime("%Y-%m-%d"),
            }
        )
    return items
