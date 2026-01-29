from crawler.config import TIMEZONE
from crawler.fetchers.rss import fetch_rss_sources
from crawler.utils import format_date, normalize_text


NEWS_RSS_SOURCES = [
    {"name": "한국경제(증권)", "url": "https://www.hankyung.com/feed/finance"},
    {"name": "매일경제(증권)", "url": "https://www.mk.co.kr/rss/50200011/"},
    {"name": "파이낸셜뉴스(증권)", "url": "https://www.fnnews.com/rss/r20/fn_realnews_stock.xml"},
    {"name": "파이낸셜뉴스(IT)", "url": "https://www.fnnews.com/rss/r20/fn_realnews_it.xml"},
    {"name": "보안뉴스", "url": "http://www.boannews.com/media/news_rss.xml"},
]

COMPANY_ALIASES = {
    "미래에셋증권": ["미래에셋", "m-stock", "mstock"],
    "한국투자증권": ["한국투자", "한투"],
    "NH투자증권": ["nh", "nh투자", "나무"],
    "KB증권": ["kb", "m-able", "mable"],
    "삼성증권": ["삼성증권"],
    "신한투자증권": ["신한투자", "sol"],
    "키움증권": ["키움", "영웅문"],
    "하나증권": ["하나증권", "원큐"],
    "메리츠증권": ["메리츠"],
    "토스증권": ["토스", "toss"],
}


def _match_company(text, companies):
    lowered = (text or "").lower()
    for company in companies:
        aliases = [company] + (COMPANY_ALIASES.get(company) or [])
        for alias in aliases:
            if not alias:
                continue
            if alias.lower() in lowered:
                return company
    return None


def build_items(companies, start, end):
    if not NEWS_RSS_SOURCES:
        return [], {"entriesFetched": 0, "bySource": {}}
    raw = fetch_rss_sources(NEWS_RSS_SOURCES, TIMEZONE, max_items=50)

    by_source = {}
    for entry in raw:
        name = entry.get("source") or "Unknown"
        by_source[name] = by_source.get(name, 0) + 1

    items = []
    for entry in raw:
        published_at = entry.get("published_at")
        if not published_at:
            continue
        if start and published_at < start:
            continue
        if end and published_at > end:
            continue

        title = normalize_text(entry.get("title"))
        snippet = normalize_text(entry.get("snippet"))[:400]
        company = _match_company(f"{title} {snippet}", companies)
        if not company:
            continue

        url = entry.get("url")
        if not url:
            continue
        item_id = f"news:{company}:{url}"
        items.append(
            {
                "id": item_id,
                "company": company,
                "title": title,
                "snippet": snippet,
                "source": entry.get("source") or "News",
                "sourceType": "news",
                "date": format_date(published_at),
                "url": url,
            }
        )
    return items, {"entriesFetched": len(raw), "bySource": by_source}
