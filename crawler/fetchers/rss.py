import feedparser
import requests

from ..config import MAX_PER_SOURCE
from ..utils import normalize_text, parse_datetime


def _parse_feed(source):
    url = source["url"]

    # feedparser can mis-decode some feeds (notably EUC-KR). Fetch bytes ourselves
    # and provide decoded text when needed.
    try:
        response = requests.get(
            url,
            timeout=20,
            headers={"User-Agent": "briefly/1.0"},
        )
        response.raise_for_status()
        content = response.content

        if source.get("name") == "보안뉴스":
            for encoding in ("euc-kr", "cp949", "utf-8"):
                try:
                    text = content.decode(encoding)
                except UnicodeDecodeError:
                    continue
                feed = feedparser.parse(text)
                if getattr(feed, "entries", None):
                    return feed
            return feedparser.parse(content)

        return feedparser.parse(content)
    except Exception:
        # Fall back to feedparser's URL fetching.
        return feedparser.parse(url)


def fetch_rss_sources(sources, timezone, max_items=None):
    items = []
    limit = max_items if isinstance(max_items, int) and max_items > 0 else MAX_PER_SOURCE["rss"]
    for source in sources:
        feed = _parse_feed(source)
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
