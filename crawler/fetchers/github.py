import os

import requests

from ..config import GITHUB_KEYWORDS, MAX_PER_SOURCE
from ..utils import normalize_text, parse_datetime


def build_headers():
    token = os.getenv("MY_GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def search_repositories(keyword):
    params = {
        "q": f"{keyword} in:name,description,readme",
        "sort": "updated",
        "order": "desc",
        "per_page": 10,
    }
    response = requests.get(
        "https://api.github.com/search/repositories",
        headers=build_headers(),
        params=params,
        timeout=20,
    )
    response.raise_for_status()
    return response.json().get("items", [])


def fetch_latest_release(repo_full_name):
    response = requests.get(
        f"https://api.github.com/repos/{repo_full_name}/releases/latest",
        headers=build_headers(),
        timeout=20,
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def fetch_github_releases(timezone):
    items = []
    seen = set()
    for keyword in GITHUB_KEYWORDS:
        for repo in search_repositories(keyword):
            full_name = repo.get("full_name")
            if not full_name or full_name in seen:
                continue
            seen.add(full_name)
            release = fetch_latest_release(full_name)
            if not release:
                continue
            published_at = parse_datetime(release.get("published_at"), timezone)
            items.append(
                {
                    "title": normalize_text(release.get("name") or repo.get("name")),
                    "url": release.get("html_url"),
                    "source": f"GitHub/{full_name}",
                    "published_at": published_at,
                    "snippet": normalize_text(release.get("body")),
                    "tab": "ai",
                    "kind": "github",
                }
            )
            if len(items) >= MAX_PER_SOURCE["github"]:
                return items
    return items
