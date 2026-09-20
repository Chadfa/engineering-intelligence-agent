from typing import Any


def build_evidence(github_data: dict[str, Any]) -> list[dict[str, str]]:
    """
    Convert retrieved GitHub data into numbered evidence items.

    Each item receives a stable evidence ID that the LLM can reference.
    """

    evidence = []
    counter = 1

    def add_evidence(
        category: str,
        claim: str,
        source: str,
    ):
        nonlocal counter

        evidence.append(
            {
                "id": f"E{counter:03d}",
                "category": category,
                "claim": claim,
                "source": source,
            }
        )

        counter += 1

    # ---------------------------------------------------------
    # REPOSITORY METADATA
    # ---------------------------------------------------------

    repository = github_data.get("repository", {})

    if repository:

        if repository.get("name") is not None:
            add_evidence(
                "repository",
                f"Repository name is '{repository['name']}'.",
                "GitHub repository metadata",
            )

        if repository.get("full_name") is not None:
            add_evidence(
                "repository",
                f"Repository full name is '{repository['full_name']}'.",
                "GitHub repository metadata",
            )

        if repository.get("description") is not None:
            add_evidence(
                "repository",
                f"Repository description is '{repository['description']}'.",
                "GitHub repository metadata",
            )

        if repository.get("language") is not None:
            add_evidence(
                "repository",
                f"Primary repository language is '{repository['language']}'.",
                "GitHub repository metadata",
            )

        if repository.get("default_branch") is not None:
            add_evidence(
                "repository",
                f"Default branch is '{repository['default_branch']}'.",
                "GitHub repository metadata",
            )

        if repository.get("stars") is not None:
            add_evidence(
                "repository",
                f"Repository has {repository['stars']} star(s).",
                "GitHub repository metadata",
            )

        if repository.get("forks") is not None:
            add_evidence(
                "repository",
                f"Repository has {repository['forks']} fork(s).",
                "GitHub repository metadata",
            )

        if repository.get("open_issues") is not None:
            add_evidence(
                "repository",
                f"Repository has {repository['open_issues']} open issue(s).",
                "GitHub repository metadata",
            )

        if repository.get("default_branch") is not None:
            add_evidence(
                "repository",
                f"Repository default branch is '{repository['default_branch']}'.",
                "GitHub repository metadata",
            )

        if repository.get("visibility") is not None:
            add_evidence(
                "repository",
                f"Repository visibility is '{repository['visibility']}'.",
                "GitHub repository metadata",
            )

        if repository.get("archived") is not None:
            add_evidence(
                "repository",
                f"Repository archived status is {repository['archived']}.",
                "GitHub repository metadata",
            )

    # ---------------------------------------------------------
    # FILE TREE
    # ---------------------------------------------------------

    file_tree = github_data.get("file_tree", [])

    for item in file_tree:

        path = item.get("path")
        item_type = item.get("type")

        if not path:
            continue

        if item_type == "directory":

            add_evidence(
                "directory",
                f"Repository contains directory '{path}'.",
                "GitHub repository file tree",
            )

        elif item_type == "file":

            size = item.get("size", 0)

            add_evidence(
                "file",
                f"Repository contains file '{path}' with size {size} bytes.",
                "GitHub repository file tree",
            )

    # ---------------------------------------------------------
    # RETRIEVED SOURCE FILES
    # ---------------------------------------------------------

        important_files = github_data.get("important_files", {})

    for path, content in important_files.items():

        if not path:
            continue

        if content:

            excerpt = content[:1200]

            add_evidence(
                "source_code",
                (
                    f"Source code for '{path}' was retrieved. "
                    f"Relevant source excerpt:\n{excerpt}"
                ),
                path,
            )

        else:

            add_evidence(
                "file",
                f"File '{path}' exists, but its contents were not retrieved.",
                path,
            )

    return evidence