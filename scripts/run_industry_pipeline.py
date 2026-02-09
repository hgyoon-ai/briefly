import argparse
import json
import html
import re
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from crawler.config import (
    DAILY_HOURS,
    ARCHIVE_FILENAME_FORMAT,
    MAX_PER_SOURCE,
    MONTHLY_DAYS,
    RSS_SOURCES,
    TABS,
    TIMEZONE,
    WEEKLY_DAYS,
)
from crawler.fetchers.huggingface import fetch_huggingface_trending
from crawler.fetchers.rss import fetch_rss_sources
from crawler.llm.openai_client import summarize_daily_highlights, summarize_item, summarize_issues
from crawler.processor.aggregate import (
    build_cards,
    build_daily_summary,
    build_monthly_data,
    build_weekly_data,
    filter_by_range,
)
from crawler.processor.dedupe import dedupe_items
from crawler.utils import parse_datetime
from crawler.run_stats import write_run_and_history


INDUSTRY_PUBLIC_DIR = Path("public/industry")
INDUSTRY_ARCHIVE_DIR = Path("archive/industry")


def write_latest_industry(tab, filename, payload):
    target_dir = INDUSTRY_PUBLIC_DIR / tab
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / filename
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_archive_industry(tab, date_str, period, payload):
    year = date_str.split("-")[0]
    month = date_str.split("-")[1]
    archive_dir = INDUSTRY_ARCHIVE_DIR / tab / year / month
    archive_dir.mkdir(parents=True, exist_ok=True)
    filename = ARCHIVE_FILENAME_FORMAT.format(date=date_str, period=period)
    target = archive_dir / filename
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_items(selected_tabs=None):
    timezone = TIMEZONE

    selected_set = set(selected_tabs) if selected_tabs else None
    rss_sources = (
        [s for s in RSS_SOURCES if (s.get("tab", "ai") in selected_set)]
        if selected_set is not None
        else RSS_SOURCES
    )
    rss_items = fetch_rss_sources(rss_sources, timezone)

    # Strong prefilter for korea.kr policy RSS in finance tab.
    finance_policy_anchors = [
        "금융위",
        "금융위원회",
        "금감원",
        "금융감독원",

        "은행",
        "대출",
        "예금",
        "가계부채",
        "금리",
        "부동산PF",
        "금융권",
        "보험사",
        "보험회사",
        "보험업",
        "보험료",
        "보험금",
        "증권",
        "자본시장",
        "금융지원",
        "금융정책",
        "자본시장법",
        "공매도",
        "불공정거래",
        "주가조작",
        "시장조성",
        "파생",
        "파생상품",
        "공시",
        "상장",
        "회계",
        "감리",
        "불완전판매",

        "전자금융",
        "핀테크",
        "오픈뱅킹",
        "마이데이터",
        "간편결제",
        "결제",
        "송금",

        "가상자산",
        "디지털자산",
        "스테이블코인",
        "STO",
        "대체거래소",
        "거래소",
        "예탁결제원",
        "자금세탁",
        "AML",
        "이상거래",
        "FDS",
        "내부통제",

        "개인정보",
        "개인정보보호",
        "유출",
        "해킹",
        "피싱",
        "스미싱",
        "보이스피싱",
        "취약점",
        "보안",
        "본인인증",
        "인증서",
        "전자서명",
        "인증수단",
        "인증체계",
        "금융보안",
    ]

    finance_policy_qualifiers = [
        "감독",
        "규제",
        "지침",
        "가이드",
        "가이드라인",
        "입법",
        "법안",
        "시행령",
        "제도",
        "개정",
        "정비",
        "대책",
        "방안",
        "발표",
        "시행",
        "추진",
        "강화",
        "제재",
        "과징금",
        "과태료",
        "행정처분",
    ]

    finance_policy_always = [
        # These are usually finance/reg/security even without explicit policy verbs.
        "마이데이터",
        "오픈뱅킹",
        "전자금융",
        "금융보안",
        "가상자산",
        "디지털자산",
        "스테이블코인",
        "STO",
        "자금세탁",
        "AML",
        "FDS",
        "이상거래",
        "개인정보",
        "유출",
        "해킹",
        "피싱",
        "스미싱",
        "보이스피싱",
        "취약점",
    ]

    realestate_anchors = [
        "부동산",
        "주택",
        "아파트",
        "집값",
        "가격",
        "거래",
        "매매",
        "청약",
        "분양",
        "임대",
        "전세",
        "월세",
        "전월세",
        "전세값",
        "월세값",
        "임대차",
        "재건축",
        "재개발",
        "정비사업",
        "공급",
        "택지",
        "공시가격",
        "공시지가",
        "주담대",
        "주택담보",
        "LTV",
        "DTI",
        "DSR",
        "취득세",
        "양도세",
        "종부세",
        "재산세",
        "PF",
        "미분양",
    ]

    realestate_policy_signals = [
        "정책",
        "대책",
        "규제",
        "완화",
        "강화",
        "지원",
        "시행",
        "개정",
        "입법",
        "법안",
        "고시",
        "공고",
        "가이드",
        "방안",
        "발표",
        "계획",
        "시정",
        "억제",
        "안정",
        "안정화",
        "관리",
        "단속",
        "점검",
        "대응",
        "조치",
        "개선",
        "방침",
        "지시",
        "당정",
        "정부",
        "대통령실",
        "국회",
        "투기",
        "과열",
        "검토",
        "추진",
        "논의",
        "협의",
        "TF",
        "시범",
        "관계부처",
        "국토교통부",
        "국토부",
        "LH",
        "주택도시기금",
    ]

    realestate_media_excludes = [
        "매물마당",
        "분양캘린더",
        "시세",
        "급매",
        "신고가",
        "청약경쟁률",
        "수주",
        "실적",
    ]

    def is_finance_policy_item(item):
        if item.get("kind") != "rss":
            return False
        if item.get("tab") != "finance":
            return False
        return item.get("source") == "정책브리핑"

    def finance_policy_match(item):
        title = item.get("title") or ""
        snippet = item.get("snippet") or ""

        # Strip HTML (korea.kr snippets are HTML-heavy).
        snippet = html.unescape(snippet)
        snippet = re.sub(r"<[^>]+>", " ", snippet)
        snippet = re.sub(r"\s+", " ", snippet).strip()

        # korea.kr policy RSS often includes a long ministry contact footer ("문의:"),
        # which can create false positives (e.g. unrelated policies listing 금융위원회).

        cut_markers = (
            "문의:",
            "문의 :",
            "문의처",
            "문의사항:",
            "담당부서",
            "첨부파일",
            "자료출처",
            "관련자료",
        )
        cut_index = None
        for marker in cut_markers:
            idx = snippet.find(marker)
            if idx == -1:
                continue
            cut_index = idx if cut_index is None else min(cut_index, idx)
        if cut_index is not None:
            snippet = snippet[:cut_index]

        body = snippet[:800]
        title_l = title.lower()
        text_l = f"{title} {body}".lower()

        if any(k.lower() in title_l for k in finance_policy_anchors):
            return True
        if any(k.lower() in text_l for k in finance_policy_always):
            return True
        if any(k.lower() in text_l for k in finance_policy_anchors) and any(
            k.lower() in text_l for k in finance_policy_qualifiers
        ):
            return True
        return False

    def is_realestate_item(item):
        if item.get("kind") != "rss":
            return False
        return item.get("tab") == "realestate"

    def realestate_policy_match(item):
        title = item.get("title") or ""
        snippet = item.get("snippet") or ""
        source = item.get("source") or ""

        snippet = html.unescape(snippet)
        snippet = re.sub(r"<[^>]+>", " ", snippet)
        snippet = re.sub(r"\s+", " ", snippet).strip()

        cut_markers = (
            "문의:",
            "문의 :",
            "문의처",
            "문의사항:",
            "담당부서",
            "첨부파일",
            "자료출처",
            "관련자료",
        )
        cut_index = None
        for marker in cut_markers:
            idx = snippet.find(marker)
            if idx == -1:
                continue
            cut_index = idx if cut_index is None else min(cut_index, idx)
        if cut_index is not None:
            snippet = snippet[:cut_index]

        body = snippet[:800]
        title_l = title.lower()
        text_l = f"{title} {body}".lower()
        source_l = source.lower()

        has_anchor_title = any(k.lower() in title_l for k in realestate_anchors)
        has_anchor = has_anchor_title or any(k.lower() in text_l for k in realestate_anchors)
        has_signal = any(k.lower() in text_l for k in realestate_policy_signals)

        is_media = source_l in {"한국경제(부동산)", "매일경제(부동산)"}
        if is_media:
            if any(k.lower() in title_l for k in realestate_media_excludes):
                return False
            return has_anchor and has_signal

        if source_l == "정책브리핑":
            return has_anchor and has_signal

        return has_anchor and has_signal

    if selected_set is None or "finance" in selected_set:
        policy_total = len([item for item in rss_items if is_finance_policy_item(item)])
        rss_items = [
            item
            for item in rss_items
            if (not is_finance_policy_item(item)) or finance_policy_match(item)
        ]
        policy_kept = len([item for item in rss_items if is_finance_policy_item(item)])
        if policy_total:
            print(f"[finance] korea.kr policy kept: {policy_kept}/{policy_total}")

    if selected_set is None or "realestate" in selected_set:
        realestate_total = len([item for item in rss_items if is_realestate_item(item)])
        rss_items = [
            item
            for item in rss_items
            if (not is_realestate_item(item)) or realestate_policy_match(item)
        ]
        realestate_kept = len([item for item in rss_items if is_realestate_item(item)])
        if realestate_total:
            print(f"[realestate] policy-signal kept: {realestate_kept}/{realestate_total}")

    hf_items = fetch_huggingface_trending(timezone) if (selected_set is None or "ai" in selected_set) else []
    print(f"RSS items: {len(rss_items)}")
    print(f"Hugging Face models: {len(hf_items)}")
    return rss_items + hf_items


def count_by_source(items):
    counts = {}
    for item in items:
        name = item.get("source") or "Unknown"
        counts[name] = counts.get(name, 0) + 1
    return counts


def enrich_items(items):
    enriched = []
    for item in items:
        tab = item.get("tab", "ai")
        summary = summarize_item(item, tab=tab)
        enriched.append(
            {
                **item,
                "summary": summary["summary"],
                "why": summary["why"],
                "topics": summary["topics"],
                "status": summary["status"],
                "importanceScore": summary["importanceScore"],
            }
        )
    return enriched


def write_industry_run_stats(payload):
    write_run_and_history(
        "public/industry/run.json",
        "public/industry/run_history.json",
        payload,
        limit=7,
    )


def clamp_total(items):
    if len(items) <= MAX_PER_SOURCE["total"]:
        return items
    return items[: MAX_PER_SOURCE["total"]]


def build_daily_payload(items, raw_count, now, tab="ai"):
    selected = select_diverse_by_source(items, max_total=5, max_per_source=2)
    cards = build_cards(selected, tab=tab)
    card_count = len(cards)
    if card_count <= 0:
        desired_lines = 0
    elif card_count == 1:
        desired_lines = 1
    elif card_count == 2:
        desired_lines = 2
    else:
        desired_lines = 3

    base_highlights = build_daily_summary(items, raw_count)
    if desired_lines > 0:
        llm_highlights = summarize_daily_highlights(selected[:8], tab=tab, desired_lines=desired_lines)
        bullets = llm_highlights.get("bullets") if isinstance(llm_highlights, dict) else None
    else:
        bullets = []

    if not isinstance(bullets, list) or len(bullets) != desired_lines:
        bullets = (base_highlights.get("bullets") or [])[:desired_lines]

    daily = {
        "date": now.strftime("%Y-%m-%d"),
        "highlights": {
            **base_highlights,
            "bullets": bullets,
        },
        "cards": cards,
    }
    return daily


def sort_by_importance(items):
    return sorted(
        items,
        key=lambda item: (
            item.get("importanceScore") or 0,
            item.get("published_at") or datetime.min,
        ),
        reverse=True,
    )


def pick_diverse_items(items, max_items=8):
    selected = []
    used_topics = set()
    for item in items:
        topics = item.get("topics") or []
        primary = topics[0] if topics else None
        if primary and primary in used_topics:
            continue
        if primary:
            used_topics.add(primary)
        selected.append(item)
        if len(selected) >= max_items:
            return selected
    for item in items:
        if item in selected:
            continue
        selected.append(item)
        if len(selected) >= max_items:
            break
    return selected


def select_diverse_by_source(items, max_total=5, max_per_source=2):
    selected = []
    counts = {}
    for item in items:
        source = item.get("source") or "Unknown"
        current = counts.get(source, 0)
        if current >= max_per_source:
            continue
        selected.append(item)
        counts[source] = current + 1
        if len(selected) >= max_total:
            break
    return selected


def iter_dates(start, end):
    current = start.date()
    end_date = end.date()
    while current <= end_date:
        yield current
        current += timedelta(days=1)


def load_archive_daily_items(start, end, timezone, tab):
    items = []
    for date in iter_dates(start, end):
        date_str = date.strftime("%Y-%m-%d")
        archive_path = (
            INDUSTRY_ARCHIVE_DIR
            / tab
            / date_str.split("-")[0]
            / date_str.split("-")[1]
            / ARCHIVE_FILENAME_FORMAT.format(date=date_str, period="daily")
        )
        if not archive_path.exists():
            continue
        payload = json.loads(archive_path.read_text(encoding="utf-8"))
        for card in payload.get("cards", []):
            published_at = parse_datetime(card.get("publishedAt"), timezone)
            if not published_at:
                continue
            items.append(
                {
                    "title": card.get("title"),
                    "url": card.get("url"),
                    "source": card.get("source"),
                    "published_at": published_at,
                    "summary": card.get("summary", []),
                    "why": card.get("whyItMatters"),
                    "topics": card.get("topics", []),
                    "status": card.get("status"),
                    "hash": card.get("hash"),
                    "importanceScore": card.get("importanceScore"),
                    "tab": card.get("tab", "ai"),
                }
            )
    return items


def group_by_tab(items, tabs):
    grouped = {tab: [] for tab in tabs}
    for item in items:
        tab = item.get("tab", "ai")
        grouped.setdefault(tab, []).append(item)
    return grouped


def parse_args():
    parser = argparse.ArgumentParser(description="Run Briefly industry pipeline")
    parser.add_argument(
        "--tab",
        action="append",
        default=None,
        help="Only run a specific tab (repeatable; comma-separated supported).",
    )
    return parser.parse_args()


def normalize_selected_tabs(raw):
    if not raw:
        return list(TABS)
    selected = []
    for value in raw:
        for part in (value or "").split(","):
            tab = part.strip()
            if tab:
                selected.append(tab)

    invalid = [t for t in selected if t not in TABS]
    if invalid:
        raise SystemExit(f"Unknown tab(s): {', '.join(invalid)}. Valid: {', '.join(TABS)}")

    deduped = []
    seen = set()
    for tab in selected:
        if tab in seen:
            continue
        seen.add(tab)
        deduped.append(tab)
    return deduped


def main():
    args = parse_args()
    load_dotenv()
    timezone = ZoneInfo(TIMEZONE)
    now = datetime.now(timezone)

    selected_tabs = normalize_selected_tabs(args.tab)
    selected_set = set(selected_tabs)

    errors = []
    run_stats = {
        "id": now.isoformat(),
        "ts": now.isoformat(),
        "timezone": TIMEZONE,
        "selectedTabs": selected_tabs,
        "pipeline": {},
        "sources": {},
        "llm": {},
        "errors": errors,
    }

    try:
        raw_items = load_items(selected_tabs=selected_tabs)
        run_stats["pipeline"]["rawTotal"] = len(raw_items)

        run_stats["sources"] = {
            "rss": {
                "total": len([item for item in raw_items if item.get("kind") == "rss"]),
                "bySource": count_by_source([item for item in raw_items if item.get("kind") == "rss"]),
            },
            "hf": {
                "total": len([item for item in raw_items if item.get("kind") == "hf"]),
            },
            "hn": {
                "total": len([item for item in raw_items if item.get("kind") == "hn"]),
            },
        }

        raw_items = clamp_total(raw_items)
        run_stats["pipeline"]["rawClamped"] = len(raw_items)
        print(f"Total raw items (clamped): {len(raw_items)}")

        deduped = dedupe_items(raw_items)
        run_stats["pipeline"]["deduped"] = len(deduped)
        print(f"Deduped items: {len(deduped)}")

        deduped = [item for item in deduped if item.get("tab", "ai") in selected_set]
        run_stats["pipeline"]["dedupedSelected"] = len(deduped)
        print(f"Deduped items (selected tabs): {len(deduped)}")

        # One summarize_item call per deduped item.
        run_stats["llm"]["itemCalls"] = len(deduped)

        enriched = enrich_items(deduped)
        run_stats["pipeline"]["enriched"] = len(enriched)
        print(f"Enriched items: {len(enriched)}")

        daily_start = now - timedelta(hours=DAILY_HOURS)
        weekly_start = now - timedelta(days=WEEKLY_DAYS - 1)
        monthly_start = now - timedelta(days=MONTHLY_DAYS - 1)

        today_str = now.strftime("%Y-%m-%d")
        raw_by_tab = group_by_tab([item for item in raw_items if item.get("tab", "ai") in selected_set], selected_tabs)
        enriched_by_tab = group_by_tab(enriched, selected_tabs)

        run_stats["tabs"] = {}

        for tab in selected_tabs:
            tab_items = enriched_by_tab.get(tab, [])
            daily_items = filter_by_range(tab_items, daily_start, now)
            daily_items = sort_by_importance(daily_items)
            raw_daily_count = len(filter_by_range(raw_by_tab.get(tab, []), daily_start, now))

            run_stats["llm"]["highlightsCalls"] = run_stats["llm"].get("highlightsCalls", 0) + 1
            daily_payload = build_daily_payload(daily_items, raw_daily_count, now, tab=tab)
            write_latest_industry(tab, "daily.json", daily_payload)
            write_archive_industry(tab, today_str, "daily", daily_payload)

            archive_items = load_archive_daily_items(monthly_start, now, TIMEZONE, tab)
            weekly_items = filter_by_range(archive_items, weekly_start, now)
            monthly_items = filter_by_range(archive_items, monthly_start, now)
            weekly_items = sort_by_importance(weekly_items)
            monthly_items = sort_by_importance(monthly_items)
            print(f"[{tab}] Weekly items from archive: {len(weekly_items)}")
            print(f"[{tab}] Monthly items from archive: {len(monthly_items)}")

            weekly_issue_items = pick_diverse_items(weekly_items, max_items=8)
            monthly_issue_items = pick_diverse_items(monthly_items, max_items=8)

            # summarize_issues is called twice per tab.
            run_stats["llm"]["issueCalls"] = run_stats["llm"].get("issueCalls", 0) + 2
            weekly_issues = summarize_issues(weekly_issue_items, max_items=5, tab=tab)
            monthly_issues = summarize_issues(monthly_issue_items, max_items=5, tab=tab)

            weekly_payload = build_weekly_data(
                weekly_items,
                len(weekly_items),
                weekly_start,
                now,
                issues=weekly_issues,
            )
            monthly_payload = build_monthly_data(
                monthly_items,
                len(monthly_items),
                monthly_start,
                now,
                issues=monthly_issues,
            )

            write_latest_industry(tab, "weekly.json", weekly_payload)
            write_latest_industry(tab, "monthly.json", monthly_payload)
            write_archive_industry(tab, today_str, "weekly", weekly_payload)
            write_archive_industry(tab, today_str, "monthly", monthly_payload)

            run_stats["tabs"][tab] = {
                "daily": {"raw": raw_daily_count, "cards": len(daily_payload.get("cards") or [])},
                "weekly": {"items": len(weekly_items), "issues": len(weekly_issues or [])},
                "monthly": {"items": len(monthly_items), "issues": len(monthly_issues or [])},
            }

        print("Pipeline completed.")
    except Exception as exc:
        errors.append({"message": repr(exc)})
        raise
    finally:
        try:
            write_industry_run_stats(run_stats)
        except Exception:
            # Best-effort: run stats must not break the pipeline.
            pass

if __name__ == "__main__":
    main()
