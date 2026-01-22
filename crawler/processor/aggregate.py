from collections import Counter, defaultdict
from datetime import datetime, timedelta

from ..utils import day_label, format_date, make_hash, normalize_text


def filter_by_range(items, start, end):
    return [item for item in items if item.get("published_at") and start <= item["published_at"] <= end]


def build_top_topics(items, limit=4):
    counts = Counter()
    scores = Counter()
    for item in items:
        weight = item.get("importanceScore") or 1
        for topic in item.get("topics", []):
            counts[topic] += 1
            scores[topic] += weight
    ranked = sorted(scores.items(), key=lambda x: (x[1], counts[x[0]]), reverse=True)
    result = []
    for topic, score in ranked[:limit]:
        result.append((topic, counts[topic], score))
    return result


def build_daily_summary(items, raw_count):
    top_topics = build_top_topics(items, limit=4)
    bullets = []
    for topic, count, _score in top_topics[:3]:
        bullets.append(f"{topic} 관련 업데이트가 {count}건 감지됨")
    while len(bullets) < 3:
        bullets.append("AI 개발 업데이트가 꾸준히 이어지고 있음")
    return {
        "bullets": bullets[:3],
        "topTopics": [topic for topic, _count, _score in top_topics],
        "stats": {
            "collected": raw_count,
            "deduped": len(items),
        },
    }


def build_cards(items):
    cards = []
    for idx, item in enumerate(items, start=1):
        key = item.get("url") or item.get("title") or ""
        signature = make_hash(normalize_text(key))
        cards.append(
            {
                "id": f"ai_{idx:04d}",
                "tab": item.get("tab", "ai"),
                "publishedAt": item["published_at"].isoformat(),
                "source": item.get("source"),
                "title": item.get("title"),
                "summary": item.get("summary", [])[:3],
                "whyItMatters": item.get("why"),
                "topics": item.get("topics", []),
                "status": item.get("status"),
                "hash": signature,
                "url": item.get("url"),
            }
        )
    return cards


def build_topic_trend(items, start, end, top_topics):
    topic_names = [topic for topic, _count, _score in top_topics]
    per_day = defaultdict(lambda: Counter())
    current = start
    while current <= end:
        per_day[format_date(current)]
        current += timedelta(days=1)

    for item in items:
        date_key = format_date(item["published_at"])
        for topic in item.get("topics", []):
            if topic in topic_names:
                per_day[date_key][topic] += 1

    trend = []
    for date_key in sorted(per_day.keys()):
        day_topics = per_day[date_key]
        for topic in topic_names:
            trend.append(
                {
                    "date": date_key,
                    "dayOfWeek": day_label(datetime.strptime(date_key, "%Y-%m-%d")),
                    "topic": topic,
                    "count": day_topics.get(topic, 0),
                }
            )
    return trend


def build_top_issues(top_topics):
    issues = []
    for idx, (topic, count, _score) in enumerate(top_topics[:4], start=1):
        issues.append(
            {
                "id": f"issue_{idx:03d}",
                "status": "ONGOING" if idx == 1 else "NEW",
                "title": f"{topic} 업데이트 집중",
                "summary": f"최근 {topic} 관련 업데이트가 지속적으로 언급됨",
                "articleCount": count,
            }
        )
    return issues


def build_weekly_data(items, raw_count, start, end, issues=None):
    top_topics = build_top_topics(items, limit=4)
    return {
        "range": {
            "from": format_date(start),
            "to": format_date(end),
        },
        "kpis": {
            "collected": raw_count,
            "deduped": len(items),
            "uniqueTopics": len({topic for item in items for topic in item.get("topics", [])}),
        },
        "topTopics": [{"name": topic, "count": count} for topic, count, _score in top_topics],
        "topicTrend": build_topic_trend(items, start, end, top_topics),
        "topIssues": issues or build_top_issues(top_topics),
    }


def build_weekly_breakdown(items, start, end, top_topics):
    topic_names = [topic for topic, _count, _score in top_topics]
    weekly = []
    current = start
    while current <= end:
        week_end = min(current + timedelta(days=6), end)
        label = f"Week {len(weekly) + 1} ({current.strftime('%m/%d')}-{week_end.strftime('%m/%d')})"
        counts = Counter()
        for item in items:
            if current <= item["published_at"] <= week_end:
                for topic in item.get("topics", []):
                    if topic in topic_names:
                        counts[topic] += 1
        weekly.append(
            {
                "week": label,
                "topicCounts": {topic: counts.get(topic, 0) for topic in topic_names},
            }
        )
        current += timedelta(days=7)
    return weekly


def build_monthly_data(items, raw_count, start, end, issues=None):
    top_topics = build_top_topics(items, limit=5)
    topic_names = [topic for topic, _count, _score in top_topics]
    counts = Counter()
    for item in items:
        for topic in item.get("topics", []):
            if topic in topic_names:
                counts[topic] += 1

    total = sum(counts.values()) or 1
    market_share = {topic: round(counts.get(topic, 0) / total * 100) for topic in topic_names}
    other = max(0, 100 - sum(market_share.values()))
    market_share["Other"] = other

    return {
        "range": {
            "from": format_date(start),
            "to": format_date(end),
        },
        "kpis": {
            "collected": raw_count,
            "deduped": len(items),
            "uniqueTopics": len({topic for item in items for topic in item.get("topics", [])}),
            "marketShare": market_share,
        },
        "weeklyData": build_weekly_breakdown(items, start, end, top_topics),
        "topIssues": issues or build_top_issues(top_topics),
    }
