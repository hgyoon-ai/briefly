import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from crawler.config import ARCHIVE_DIR, ARCHIVE_FILENAME_FORMAT, TIMEZONE
from crawler.utils import make_hash, normalize_text


TOPICS = [
    "Models",
    "Training",
    "Inference",
    "Tooling",
    "Infra",
    "Safety",
    "Research",
    "Product",
    "Business",
    "Data",
]

STATUSES = ["NEW", "ONGOING", "SHIFTING"]


def load_base_daily():
    base_path = Path("public/industry/ai/daily.json")
    return json.loads(base_path.read_text(encoding="utf-8"))


def build_cards(base_cards, day_offset, current_date):
    cards = []
    for idx, card in enumerate(base_cards, start=1):
        topic = TOPICS[(idx + day_offset) % len(TOPICS)]
        published = current_date.replace(hour=9 + idx, minute=10 + idx, second=0)
        key = card.get("url") or card.get("title") or ""
        signature = make_hash(normalize_text(f"{key}-{current_date.date()}"))
        importance = 5 + (day_offset + idx) % 5
        cards.append(
            {
                **card,
                "id": f"ai_{idx:04d}",
                "publishedAt": published.isoformat(),
                "summary": [
                    card.get("title", ""),
                    f"{topic} 관련 업데이트가 집중됨",
                    "관련 업데이트가 이어지고 있음",
                ],
                "topics": [topic],
                "status": STATUSES[(idx + day_offset) % len(STATUSES)],
                "hash": signature,
                "importanceScore": importance,
            }
        )
    return cards


def build_highlights(day_offset, cards):
    top_topics = []
    for card in cards:
        for topic in card.get("topics", []):
            if topic not in top_topics:
                top_topics.append(topic)
    top_topics = top_topics[:4]
    bullets = [
        f"{top_topics[0]} 관련 업데이트가 {len(cards)}건 감지됨",
        "AI 개발 업데이트가 꾸준히 이어지고 있음",
        "주요 릴리즈와 모델 업데이트가 함께 등장함",
    ]
    return {
        "bullets": bullets,
        "topTopics": top_topics,
        "stats": {
            "collected": len(cards) + 2 + day_offset % 3,
            "deduped": len(cards),
        },
    }


def write_archive(tab, date_str, payload):
    year, month, _ = date_str.split("-")
    target_dir = ARCHIVE_DIR / "industry" / tab / year / month
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = ARCHIVE_FILENAME_FORMAT.format(date=date_str, period="daily")
    target_path = target_dir / filename
    target_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    base_daily = load_base_daily()
    timezone = ZoneInfo(TIMEZONE)
    today = datetime.now(timezone).replace(hour=9, minute=0, second=0, microsecond=0)

    for offset in range(30):
        current_date = today - timedelta(days=offset)
        date_str = current_date.strftime("%Y-%m-%d")
        cards = build_cards(base_daily.get("cards", []), offset, current_date)
        payload = {
            "date": date_str,
            "highlights": build_highlights(offset, cards),
            "cards": cards,
        }
        write_archive("ai", date_str, payload)

        if offset == 0:
            Path("public/industry/ai").mkdir(parents=True, exist_ok=True)
            Path("public/industry/ai/daily.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    print("Generated 30 daily archive files.")


if __name__ == "__main__":
    main()
