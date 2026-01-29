import feedparser

from ..config import MAX_PER_SOURCE
from ..utils import normalize_text, parse_datetime


def fetch_rss_sources(sources, timezone, max_items=None):
    items = []
    limit = max_items if isinstance(max_items, int) and max_items > 0 else MAX_PER_SOURCE["rss"]
    for source in sources:
        feed = feedparser.parse(source["url"])
        for entry in feed.entries[:limit]:
            published = (
                entry.get("published")
                or entry.get("updated")
                or entry.get("published_parsed")
            )
            published_at = parse_datetime(published, timezone)
            items.append(
                {
                    "title": normalize_text(entry.get("title")),
                    "url": entry.get("link"),
                    "source": source["name"],
                    "published_at": published_at,
                    "snippet": normalize_text(entry.get("summary")),
                    "tab": source.get("tab", "ai"),
                    "kind": "rss",
                }
            )
    return items
