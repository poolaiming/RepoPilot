from __future__ import annotations

import os
import re
from dataclasses import dataclass

import httpx


ISSUE_RE = re.compile(r"https://github\.com/([^/]+)/([^/]+)/issues/(\d+)")


@dataclass(frozen=True)
class IssueRef:
    owner: str
    repo: str
    number: int


def parse_issue_url(url: str) -> IssueRef:
    match = ISSUE_RE.fullmatch(url.strip())
    if not match:
        raise ValueError("Expected a GitHub issue URL like https://github.com/owner/repo/issues/123")
    owner, repo, number = match.groups()
    return IssueRef(owner=owner, repo=repo, number=int(number))


async def fetch_issue(url: str) -> dict:
    ref = parse_issue_url(url)
    headers = {"Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    base = f"https://api.github.com/repos/{ref.owner}/{ref.repo}/issues/{ref.number}"
    async with httpx.AsyncClient(headers=headers, timeout=20) as client:
        issue_resp = await client.get(base)
        issue_resp.raise_for_status()
        issue = issue_resp.json()

        comments_resp = await client.get(f"{base}/comments")
        comments_resp.raise_for_status()
        comments = comments_resp.json()

    return {
        "title": issue.get("title") or "",
        "body": issue.get("body") or "",
        "comments": [
            {"user": (c.get("user") or {}).get("login", ""), "body": c.get("body") or ""}
            for c in comments
        ],
    }
