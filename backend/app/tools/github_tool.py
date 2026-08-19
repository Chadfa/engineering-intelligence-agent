import base64
import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")


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


def _get(url: str) -> Any:
    response = httpx.get(
        url,
        headers=_headers(),
        timeout=20,
    )

    response.raise_for_status()

    return response.json()


def get_repository(owner: str, repo: str) -> dict[str, Any]:
    data = _get(
        f"{GITHUB_API}/repos/{owner}/{repo}"
    )

    return {
        "name": data["name"],
        "full_name": data["full_name"],
        "description": data["description"],
        "language": data["language"],
        "stars": data["stargazers_count"],
        "forks": data["forks_count"],
        "open_issues": data["open_issues_count"],
        "default_branch": data["default_branch"],
        "visibility": data["visibility"],
        "archived": data["archived"],
        "html_url": data["html_url"],
    }


def get_repository_contents(
    owner: str,
    repo: str,
    path: str = "",
) -> list[dict[str, Any]]:
    url = (
        f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
    )

    data = _get(url)

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
    data = _get(
        f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
    )

    if data.get("encoding") != "base64":
        raise ValueError(
            f"Unsupported encoding for {path}"
        )

    return base64.b64decode(
        data["content"]
    ).decode(
        "utf-8",
        errors="replace",
    )


# Files we generally don't want EIA to ingest.
IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".next",
    "dist",
    "build",
}


IMPORTANT_FILES = {
    "README.md",
    "requirements.txt",
    "pyproject.toml",
    "package.json",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    ".env.example",
}


def build_file_tree(
    owner: str,
    repo: str,
    branch: str = "main",
) -> list[dict[str, Any]]:
    url = (
        f"{GITHUB_API}/repos/{owner}/{repo}"
        f"/git/trees/{branch}?recursive=1"
    )

    data = _get(url)

    if data.get("truncated"):
        print(
            "Warning: GitHub returned a truncated repository tree."
        )

    tree = []

    for item in data.get("tree", []):
        path = item["path"]

        parts = path.split("/")

        if any(
            part in IGNORED_DIRECTORIES
            for part in parts
        ):
            continue

        if item["type"] == "tree":
            tree.append(
                {
                    "path": path,
                    "type": "directory",
                }
            )

        elif item["type"] == "blob":
            tree.append(
                {
                    "path": path,
                    "type": "file",
                    "size": item.get("size", 0),
                }
            )

    return tree


def collect_important_files(
    owner: str,
    repo: str,
    tree: list[dict[str, Any]],
    max_files: int = 20,
) -> dict[str, str]:

    selected = []

    # First prioritize explicitly important files.
    for item in tree:
        if item["type"] != "file":
            continue

        filename = item["path"].split("/")[-1]

        if filename in IMPORTANT_FILES:
            selected.append(item["path"])

    # Then add reasonable source/config files.
    source_extensions = (
        ".py",
        ".js",
        ".ts",
        ".tsx",
        ".jsx",
        ".java",
        ".go",
        ".rs",
        ".sql",
        ".yml",
        ".yaml",
    )

    for item in tree:
        if len(selected) >= max_files:
            break

        if item["type"] != "file":
            continue

        path = item["path"]

        if path in selected:
            continue

        if path.lower().endswith(source_extensions):
            selected.append(path)

    selected = selected[:max_files]

    files = {}

    for path in selected:
        try:
            files[path] = get_file(
                owner,
                repo,
                path,
            )
        except Exception as exc:
            files[path] = (
                f"[Unable to read file: {exc}]"
            )

    return files


def inspect_repository(
    owner: str,
    repo: str,
) -> dict[str, Any]:

    repository = get_repository(
        owner,
        repo,
    )

    tree = build_file_tree(
        owner,
        repo,
        repository["default_branch"],
    )

    important_files = collect_important_files(
        owner,
        repo,
        tree,
    )

    return {
        "repository": repository,
        "file_tree": tree,
        "important_files": important_files,
    }