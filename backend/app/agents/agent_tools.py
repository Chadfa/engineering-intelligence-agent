from langchain_core.tools import tool

from app.tools.github_tool import inspect_repository


@tool
def inspect_github_repository(
    owner: str,
    repo: str,
) -> str:
    """
    Inspect a GitHub repository and return verified repository evidence.

    Use this tool when the user asks about a specific GitHub repository,
    its structure, files, implementation, or engineering characteristics.
    """

    result = inspect_repository(
        owner=owner,
        repo=repo,
    )

    return str(result)