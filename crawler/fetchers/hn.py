from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests

from ..config import HN_API_URL, HN_COMMENTS_MIN, HN_POINTS_MIN, HN_WINDOW_HOURS, MAX_PER_SOURCE
from ..utils import normalize_text


def fetch_hacker_news_trending(timezone):
    now = datetime.now(ZoneInfo(timezone))
    window_start = int((now - timedelta(hours=HN_WINDOW_HOURS)).timestamp())
    params = {
        "query": "",
        "tags": "story",
        "filters": "NOT tags:ask_hn AND NOT tags:show_hn AND NOT tags:job",
        "numericFilters": f"created_at_i>={window_start}",
        "hitsPerPage": MAX_PER_SOURCE["hn"],
    }
    try:
        response = requests.get(HN_API_URL, params=params, timeout=20)
        response.raise_for_status()
    except Exception as exc:
        print(f"HN fetch failed: {exc}")
        return []

    payload = response.json()
    items = []
    for hit in payload.get("hits", []):
        points = hit.get("points") or 0
        comments = hit.get("num_comments") or 0
        if points < HN_POINTS_MIN and comments < HN_COMMENTS_MIN:
            continue
        url = hit.get("url") or hit.get("story_url")
        if not url:
            continue
        created_at = hit.get("created_at_i")
        published_at = datetime.fromtimestamp(created_at, tz=ZoneInfo(timezone)) if created_at else None
        title = hit.get("title") or hit.get("story_title") or ""
        snippet = f"{points} points · {comments} comments"
        items.append(
            {
                "title": normalize_text(title),
                "url": url,
                "source": "Hacker News",
                "published_at": published_at,
                "snippet": snippet,
                "tab": "ai",
                "kind": "hn",
            }
        )
    return items
