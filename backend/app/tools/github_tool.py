import base64
import os
from typing import Any

import httpx


GITHUB_API = "https://api.github.com"


def _headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
    }

    token = os.getenv("GITHUB_TOKEN")

    if token:
        headers["Authorization"] = f"Bearer {token}"

    return headers


def get_repository(owner: str, repo: str) -> dict[str, Any]:
    url = f"{GITHUB_API}/repos/{owner}/{repo}"

    response = httpx.get(
        url,
        headers=_headers(),
        timeout=20,
    )

    response.raise_for_status()

    data = response.json()

    return {
        "name": data["name"],
        "full_name": data["full_name"],
        "description": data["description"],
        "language": data["language"],
        "stars": data["stargazers_count"],
        "forks": data["forks_count"],
        "open_issues": data["open_issues_count"],
        "default_branch": data["default_branch"],
        "html_url": data["html_url"],
    }


def get_repository_contents(
    owner: str,
    repo: str,
    path: str = "",
) -> list[dict[str, Any]]:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"

    response = httpx.get(
        url,
        headers=_headers(),
        timeout=20,
    )

    response.raise_for_status()

    data = response.json()

    if isinstance(data, dict):
        data = [data]

    return [
        {
            "name": item["name"],
            "path": item["path"],
            "type": item["type"],
            "size": item.get("size", 0),
        }
        for item in data
    ]


def get_file(
    owner: str,
    repo: str,
    path: str,
) -> str:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"

    response = httpx.get(
        url,
        headers=_headers(),
        timeout=20,
    )

    response.raise_for_status()

    data = response.json()

    if data.get("encoding") != "base64":
        raise ValueError("GitHub returned an unsupported file encoding.")

    content = base64.b64decode(data["content"]).decode(
        "utf-8",
        errors="replace",
    )

    return content


def inspect_repository(owner: str, repo: str) -> dict[str, Any]:
    repository = get_repository(owner, repo)
    contents = get_repository_contents(
        owner,
        repo,
    )

    return {
        "repository": repository,
        "root_contents": contents,
    }