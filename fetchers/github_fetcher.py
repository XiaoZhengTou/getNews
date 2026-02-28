# fetchers/github_fetcher.py
import os
import requests
from dotenv import load_dotenv
from typing import List
from fetchers.base import BaseFetcher, HotItem

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}
KEYWORDS = ["claude", "ai", "developer", "frontend", "vscode",
            "tool", "assistant", "code", "productivity"]


class GithubFetcher(BaseFetcher):
    platform_name = "github"
    platform_label = "GitHub"

    def fetch(self, count: int = 5) -> List[HotItem]:
        url = "https://api.github.com/search/repositories"
        params = {
            "q": "ai developer tools stars:>500 pushed:>2025-01-01",
            "sort": "updated",
            "order": "desc",
            "per_page": count * 3,
        }
        res = requests.get(url, headers=HEADERS, params=params, timeout=10)
        res.raise_for_status()
        items = res.json().get("items", [])

        filtered = []
        for r in items:
            desc = (r.get("description") or "").lower()
            name = r["name"].lower()
            if any(kw in desc or kw in name for kw in KEYWORDS):
                filtered.append(HotItem(
                    title=r["name"],
                    url=r["html_url"],
                    score=r["stargazers_count"],
                    description=r.get("description", ""),
                    platform="github",
                ))
            if len(filtered) >= count:
                break

        return filtered[:count]

    def fetch_detail(self, item: HotItem) -> str:
        """获取 README 内容"""
        parts = item.url.rstrip("/").split("/")
        owner, repo = parts[-2], parts[-1]
        url = f"https://api.github.com/repos/{owner}/{repo}/readme"
        headers = {**HEADERS, "Accept": "application/vnd.github.raw"}
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 404:
            return ""
        res.raise_for_status()
        return res.text
