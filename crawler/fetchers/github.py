from datetime import datetime
from urllib.parse import urlparse

import requests

from ..config import GITHUB_API_URL


def _headers(token):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def parse_github_repo(url):
    if not url:
        return None
    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()
    path = parsed.path.strip("/")
    parts = [p for p in path.split("/") if p]
    if host.endswith("github.com") and len(parts) >= 2:
        return parts[0], parts[1].replace(".git", "")
    if host.endswith("raw.githubusercontent.com") and len(parts) >= 2:
        return parts[0], parts[1]
    return None


def fetch_repo(owner, repo, token=None):
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}"
    response = requests.get(url, headers=_headers(token), timeout=20)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def fetch_latest_release(owner, repo, token=None):
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/releases/latest"
    response = requests.get(url, headers=_headers(token), timeout=20)
    if response.status_code in (404, 422):
        return None
    response.raise_for_status()
    return response.json()


def search_recent_repos(*, token=None, created_after, min_stars, per_page=30, pages=1):
    repos = []
    for page in range(1, pages + 1):
        query = f"created:>={created_after} stars:>={min_stars}"
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": per_page,
            "page": page,
        }
        response = requests.get(
            f"{GITHUB_API_URL}/search/repositories",
            headers=_headers(token),
            params=params,
            timeout=20,
        )
        if response.status_code == 403:
            break
        response.raise_for_status()
        payload = response.json()
        repos.extend(payload.get("items", []))
        if len(payload.get("items", [])) < per_page:
            break
    return repos


def parse_iso(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
