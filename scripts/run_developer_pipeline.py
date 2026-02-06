import json
import os
import random
import re
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from crawler.config import (
    DEVELOPER_MAX_CLUSTERS,
    GITHUB_RELEASE_DAYS,
    GITHUB_SEARCH_DAYS,
    GITHUB_SEARCH_MIN_STARS,
    GITHUB_SEARCH_PAGES,
    GITHUB_SEARCH_PER_PAGE,
    TIMEZONE,
)
from crawler.developer.tags import normalize_tags
from crawler.fetchers.github import (
    fetch_latest_release,
    fetch_repo,
    parse_github_repo,
    parse_iso,
    search_recent_repos,
)
from crawler.fetchers.hn import fetch_hacker_news_trending
from crawler.llm.openai_client import summarize_developer_oneliners
from crawler.run_stats import write_run_and_history
from crawler.utils import normalize_text, sha1_text


def build_cluster_id(value):
    return sha1_text(value)


def format_date(value):
    if not value:
        return None
    try:
        return value.strftime("%Y-%m-%d")
    except Exception:
        return None


HAS_KOREAN_RE = re.compile(r"[가-힣]")


def has_korean(text):
    return bool(HAS_KOREAN_RE.search(text or ""))


def clean_oneliner(text):
    if not text:
        return ""
    cleaned = normalize_text(text)
    cleaned = cleaned.strip("\"'“”‘’")
    return cleaned


def parse_hn_signal(value):
    if not value:
        return 0, 0
    match = re.search(r"(\d+)\s*p\s*·\s*(\d+)\s*c", value)
    if not match:
        return 0, 0
    return int(match.group(1)), int(match.group(2))


def primary_url(links):
    if not links:
        return None
    for link in links:
        url = link.get("url")
        if url and "news.ycombinator.com" not in url:
            return url
    return links[0].get("url")


def classify_link(url):
    if not url:
        return None
    host = (urlparse(url).netloc or "").lower()
    if "github.com" in host:
        return "github"
    if "news.ycombinator.com" in host:
        return "hn"
    if "youtube.com" in host or "youtu.be" in host:
        return "video"
    if host.endswith("arxiv.org"):
        return "paper"
    if "docs." in host or host.endswith("docs"):
        return "docs"
    if "blog" in host or "medium.com" in host or "substack.com" in host:
        return "blog"
    return "site"


WHY_TEMPLATES = {
    "release": [
        "최근 릴리즈가 나오며 실사용 공유가 빠르게 늘고 있습니다.",
        "버전 업데이트 이후 재확산이 시작된 흐름입니다.",
        "업데이트가 트리거가 되어 레퍼런스가 모이는 구간입니다.",
        "릴리즈 직후라 적용/마이그레이션 경험이 모이고 있습니다.",
        "새 릴리즈 영향으로 관심이 재점화되고 있습니다.",
    ],
    "discussion": [
        "토론이 커지면서 비교/반박/후기 링크가 몰리는 구간입니다.",
        "HN에서 논쟁이 붙어 다양한 관점이 빠르게 모이고 있습니다.",
        "반응이 빠르게 커지며 검증/재현 피드백이 늘고 있습니다.",
        "커뮤니티 반응이 커져 관련 사례 공유가 급증하고 있습니다.",
        "논의가 확산되며 구현/운영 관점의 코멘트가 쌓이고 있습니다.",
        "관심이 폭증해 대체재/비교글이 함께 등장하고 있습니다.",
    ],
    "momentum": [
        "스타 증가와 업데이트 흐름이 동시에 관측되는 상승 구간입니다.",
        "활동성과 관심도가 같이 살아 있는 프로젝트입니다.",
        "개발 신호가 이어지면서 사용 사례가 늘고 있습니다.",
        "업데이트가 유지되며 관심이 꾸준히 쌓이는 흐름입니다.",
        "커밋/업데이트가 이어져 당분간 추이를 보기에 좋습니다.",
    ],
}

TAG_TAILS = {
    "agent tooling": [
        "에이전트 활용 흐름과 맞물려 주목이 커지고 있습니다.",
        "워크플로우 자동화 관점에서 재평가가 진행 중입니다.",
    ],
    "observability": [
        "운영 가시성 개선 관점에서 재검토가 이어지고 있습니다.",
    ],
    "eval": [
        "평가/재현성 이슈가 다시 부각되고 있습니다.",
    ],
    "infra": [
        "운영/비용 관점 해석이 갈리며 논의가 이어지고 있습니다.",
    ],
    "runtime": [
        "성능/안정성 관점 논의가 빠르게 늘고 있습니다.",
    ],
    "editor": [
        "개발자 경험 개선 관점에서 관심이 커지고 있습니다.",
    ],
    "codegen": [
        "생산성 향상 기대감이 확산되는 구간입니다.",
    ],
    "testing": [
        "회귀/테스트 자동화 관점에서 주목이 이어지고 있습니다.",
    ],
    "local-first": [
        "로컬 우선 흐름과 맞물려 재조명되고 있습니다.",
    ],
    "vector db": [
        "검색/지식베이스 활용 흐름과 맞물려 관심이 커지고 있습니다.",
    ],
    "security": [
        "보안 관점에서 재점검 흐름이 이어지고 있습니다.",
    ],
    "data": [
        "데이터 품질/거버넌스 관점 논의가 늘고 있습니다.",
    ],
}

LINK_TAILS = {
    "video": ["발표 영상/데모 기반으로 확산 중입니다."],
    "blog": ["블로그 해석과 후기가 빠르게 붙는 흐름입니다."],
    "docs": ["문서 공개 이후 적용 논의가 늘고 있습니다."],
    "paper": ["연구/논문 형태로 공유되는 이슈입니다."],
    "site": ["원문 공개 이후 후속 해석이 붙고 있습니다."],
}


def build_why_now(cluster, date_str):
    cluster_id = cluster.get("id") or ""
    seed = int(sha1_text(f"{cluster_id}:{date_str}")[:8], 16)
    rng = random.Random(seed)
    evidence = cluster.get("evidence") or []
    metrics = {}
    sources = set()
    for item in evidence:
        sources.add(item.get("source"))
        metric = item.get("metric")
        if metric:
            metrics.setdefault(metric, []).append(item.get("value"))

    release_recent = "release" in metrics
    hn_comments = 0
    if "signal" in metrics:
        _, hn_comments = parse_hn_signal(metrics["signal"][0])

    section = cluster.get("section") or "trending"
    if release_recent:
        base_pool = WHY_TEMPLATES["release"]
    elif section == "discussions" or hn_comments >= 120 or "Hacker News" in sources:
        base_pool = WHY_TEMPLATES["discussion"]
    else:
        base_pool = WHY_TEMPLATES["momentum"]

    base = base_pool[rng.randrange(len(base_pool))]
    tag = (cluster.get("tags") or [None])[0]
    link_type = classify_link(primary_url(cluster.get("links") or []))
    tail_pool = []
    if tag in TAG_TAILS:
        tail_pool.extend(TAG_TAILS[tag])
    if link_type in LINK_TAILS:
        tail_pool.extend(LINK_TAILS[link_type])
    if tail_pool and rng.random() < 0.6:
        tail = tail_pool[rng.randrange(len(tail_pool))]
        return f"{base} {tail}"
    return base


def fallback_hn_oneliner(cluster):
    title = cluster.get("name") or ""
    link_type = classify_link(primary_url(cluster.get("links") or []))
    if link_type == "video":
        return f"{title} 관련 발표/데모 영상입니다."
    if link_type == "paper":
        return f"{title} 관련 연구/논문 공유입니다."
    if link_type == "docs":
        return f"{title} 관련 문서/가이드 공개입니다."
    return f"{title}에 대한 공유/분석 글입니다."


def infer_source_kind(cluster):
    sources = {item.get("source") for item in cluster.get("evidence") or []}
    if "GitHub" in sources:
        return "github"
    if "Hacker News" in sources:
        return "hn"
    return "other"


def build_oneliner_input(cluster, raw_oneliner):
    return {
        "id": cluster.get("id"),
        "name": cluster.get("name"),
        "title": cluster.get("name"),
        "description": raw_oneliner,
        "url": primary_url(cluster.get("links") or []),
        "section": cluster.get("section"),
        "tags": cluster.get("tags") or [],
        "source": infer_source_kind(cluster),
    }


def write_archive_developer(date_str, payload):
    year = date_str.split("-")[0]
    month = date_str.split("-")[1]
    archive_dir = Path("archive/developer") / year / month
    archive_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{date_str}_daily.json"
    target = archive_dir / filename
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_previous_ids_from_archive(date_str):
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return set()
    prev_date = (date_obj - timedelta(days=1)).strftime("%Y-%m-%d")
    year = prev_date.split("-")[0]
    month = prev_date.split("-")[1]
    path = Path("archive/developer") / year / month / f"{prev_date}_daily.json"
    if not path.exists():
        return set()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return set()
    return {item.get("id") for item in payload.get("clusters", []) if item.get("id")}


def build_repo_cluster(repo, release, hn_items, now):
    full_name = repo.get("full_name") or repo.get("name") or "Unknown"
    description = repo.get("description") or ""
    stars = repo.get("stargazers_count") or 0
    forks = repo.get("forks_count") or 0
    repo_url = repo.get("html_url")
    topics = repo.get("topics") or []
    updated_at = parse_iso(repo.get("updated_at"))

    evidence = []
    if stars:
        evidence.append({"source": "GitHub", "metric": "stars", "value": f"{stars:,}"})
    if forks:
        evidence.append({"source": "GitHub", "metric": "forks", "value": f"{forks:,}"})
    if updated_at:
        evidence.append({
            "source": "GitHub",
            "metric": "updated",
            "value": format_date(updated_at) or "-",
        })

    release_recent = False
    if release:
        published_at = parse_iso(release.get("published_at"))
        if published_at and (now - published_at).days <= GITHUB_RELEASE_DAYS:
            release_recent = True
            evidence.append(
                {
                    "source": "GitHub",
                    "metric": "release",
                    "value": release.get("tag_name") or format_date(published_at) or "latest",
                }
            )

    total_points = sum(item.get("points", 0) for item in hn_items)
    total_comments = sum(item.get("comments", 0) for item in hn_items)
    if total_points or total_comments:
        evidence.append(
            {
                "source": "Hacker News",
                "metric": "signal",
                "value": f"{total_points}p · {total_comments}c",
            }
        )

    score = stars / 25 + forks / 50 + total_points * 0.6 + total_comments * 1.2
    if release_recent:
        score += 20

    section = "releases" if release_recent else "trending"
    if not release_recent and total_comments >= 120:
        section = "discussions"

    why_now = ""
    if release_recent:
        why_now = "최근 릴리즈가 발표되어 빠르게 확산되고 있습니다."
    elif total_comments >= 120:
        why_now = "HN 토론이 급증하며 주목도가 빠르게 올라가고 있습니다."
    elif stars >= 200:
        why_now = "GitHub 스타 증가와 업데이트가 동시에 관측되고 있습니다."
    else:
        why_now = "개발자 커뮤니티에서 점진적으로 언급이 늘고 있습니다."

    links = []
    if repo_url:
        links.append({"label": "GitHub", "url": repo_url})
    if release and release.get("html_url"):
        links.append({"label": "Release", "url": release.get("html_url")})
    for item in hn_items:
        hn_url = item.get("hn_url")
        if hn_url:
            links.append({"label": "HN Thread", "url": hn_url})
            break

    tags = normalize_tags(topics, text=f"{full_name} {description}")

    return {
        "id": build_cluster_id(f"github:{full_name}"),
        "name": full_name,
        "section": section,
        "status": "ONGOING",
        "score": round(score, 2),
        "oneLiner": description or "오픈 소스 개발 도구/프로젝트입니다.",
        "whyNow": why_now,
        "evidence": evidence,
        "links": links,
        "tags": tags,
    }


def build_hn_cluster(item):
    title = item.get("title") or "Unknown"
    url = item.get("url")
    points = item.get("points") or 0
    comments = item.get("comments") or 0
    score = points * 0.6 + comments * 1.2
    why_now = "HN 토론이 빠르게 늘고 있습니다." if comments >= 80 else "HN에서 관심이 빠르게 올라가고 있습니다."
    evidence = [
        {
            "source": "Hacker News",
            "metric": "signal",
            "value": f"{points}p · {comments}c",
        }
    ]
    links = []
    if item.get("hn_url"):
        links.append({"label": "HN Thread", "url": item.get("hn_url")})
    if url:
        links.append({"label": "Source", "url": url})

    tags = normalize_tags([], text=title)
    return {
        "id": build_cluster_id(f"hn:{title}"),
        "name": normalize_text(title),
        "section": "discussions" if comments >= 120 else "trending",
        "status": "ONGOING",
        "score": round(score, 2),
        "oneLiner": "개발자 커뮤니티에서 화제가 되는 신규 토픽입니다.",
        "whyNow": why_now,
        "evidence": evidence,
        "links": links,
        "tags": tags,
    }


def main():
    load_dotenv()
    now = datetime.now(ZoneInfo(TIMEZONE))
    token = os.getenv("MY_GITHUB_TOKEN")

    output_dir = Path("public/developer")
    output_dir.mkdir(parents=True, exist_ok=True)

    run_stats = {
        "id": now.isoformat(),
        "ts": now.isoformat(),
        "timezone": TIMEZONE,
        "sources": {},
        "filters": {},
        "output": {},
        "errors": [],
    }

    hn_items = fetch_hacker_news_trending(TIMEZONE)
    run_stats["sources"]["hn"] = {"items": len(hn_items)}

    hn_repo_map = {}
    other_hn_items = []
    for item in hn_items:
        repo_ref = parse_github_repo(item.get("url"))
        if repo_ref:
            key = f"{repo_ref[0]}/{repo_ref[1]}"
            hn_repo_map.setdefault(key, []).append(item)
        else:
            other_hn_items.append(item)

    search_days = GITHUB_SEARCH_DAYS
    created_after = (now - timedelta(days=search_days)).strftime("%Y-%m-%d")
    pages = GITHUB_SEARCH_PAGES if token else 1
    per_page = GITHUB_SEARCH_PER_PAGE if token else min(10, GITHUB_SEARCH_PER_PAGE)
    repos = search_recent_repos(
        token=token,
        created_after=created_after,
        min_stars=GITHUB_SEARCH_MIN_STARS,
        per_page=per_page,
        pages=pages,
    )
    run_stats["sources"]["github_search"] = {
        "items": len(repos),
        "since": created_after,
        "minStars": GITHUB_SEARCH_MIN_STARS,
    }

    repo_keys = {repo.get("full_name") for repo in repos if repo.get("full_name")}
    repo_keys.update(hn_repo_map.keys())

    repo_clusters = []
    for key in sorted(repo_keys):
        try:
            owner, repo_name = key.split("/", 1)
        except ValueError:
            continue
        repo = fetch_repo(owner, repo_name, token=token)
        if not repo:
            continue
        release = fetch_latest_release(owner, repo_name, token=token)
        hn_for_repo = hn_repo_map.get(key, [])
        repo_clusters.append(build_repo_cluster(repo, release, hn_for_repo, now))

    other_clusters = [build_hn_cluster(item) for item in other_hn_items]

    clusters = repo_clusters + other_clusters
    clusters.sort(key=lambda item: item.get("score") or 0, reverse=True)
    clusters = clusters[:DEVELOPER_MAX_CLUSTERS]

    today_str = now.strftime("%Y-%m-%d")
    prev_ids = load_previous_ids_from_archive(today_str)
    new_count = 0
    for cluster in clusters:
        if cluster["id"] not in prev_ids:
            cluster["status"] = "NEW"
            new_count += 1

    raw_oneliners = {cluster["id"]: cluster.get("oneLiner") or "" for cluster in clusters}
    llm_inputs = []
    for cluster in clusters:
        cluster_id = cluster["id"]
        raw_oneliner = raw_oneliners[cluster_id]
        source_kind = infer_source_kind(cluster)
        needs_llm = source_kind == "hn" or not has_korean(raw_oneliner)
        if needs_llm:
            description = "" if source_kind == "hn" else raw_oneliner
            llm_inputs.append(build_oneliner_input(cluster, description))
        else:
            cluster["oneLiner"] = clean_oneliner(raw_oneliner)

    llm_results = summarize_developer_oneliners(llm_inputs)
    for cluster in clusters:
        cluster_id = cluster["id"]
        if llm_results.get(cluster_id):
            cluster["oneLiner"] = clean_oneliner(llm_results[cluster_id])
            continue
        source_kind = infer_source_kind(cluster)
        raw_oneliner = raw_oneliners[cluster_id]
        if source_kind == "hn":
            cluster["oneLiner"] = clean_oneliner(fallback_hn_oneliner(cluster))
        else:
            fallback = raw_oneliner or "오픈 소스 개발 도구/프로젝트입니다."
            cluster["oneLiner"] = clean_oneliner(fallback)

    for cluster in clusters:
        cluster["whyNow"] = build_why_now(cluster, today_str)

    sources_used = set()
    for cluster in clusters:
        for item in cluster.get("evidence", []):
            if item.get("source"):
                sources_used.add(item.get("source"))

    payload = {
        "date": today_str,
        "kpis": {
            "clusters": len(clusters),
            "sources": len(sources_used),
            "new": new_count,
        },
        "clusters": clusters,
    }

    (output_dir / "daily.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_archive_developer(today_str, payload)

    run_stats["output"] = {
        "clusters": len(clusters),
        "new": new_count,
    }

    write_run_and_history(
        output_dir / "run.json",
        output_dir / "run_history.json",
        run_stats,
        limit=7,
    )


if __name__ == "__main__":
    main()
