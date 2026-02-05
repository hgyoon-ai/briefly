import json
import os
from datetime import datetime, timedelta
from pathlib import Path
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


def load_previous_ids(path):
    if not path.exists():
        return set()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return set()
    return {item.get("id") for item in payload.get("clusters", []) if item.get("id")}


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

    prev_ids = load_previous_ids(output_dir / "daily.json")
    new_count = 0
    for cluster in clusters:
        if cluster["id"] not in prev_ids:
            cluster["status"] = "NEW"
            new_count += 1

    sources_used = set()
    for cluster in clusters:
        for item in cluster.get("evidence", []):
            if item.get("source"):
                sources_used.add(item.get("source"))

    payload = {
        "date": now.strftime("%Y-%m-%d"),
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
