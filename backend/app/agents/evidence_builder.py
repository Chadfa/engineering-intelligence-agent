from typing import Any


def build_evidence(github_data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Convert retrieved GitHub data into numbered evidence items.

    Each item receives a sequential evidence ID that the LLM can reference.
    Structured metadata is attached without changing the citable claim text.
    """

    evidence = []
    counter = 1
    tree_sha = github_data.get("commit_sha") or github_data.get("tree_sha")

    file_tree = github_data.get("file_tree", [])
    tree_sha_by_path = {
        item.get("path"): item.get("sha")
        for item in file_tree
        if item.get("path")
    }

    def add_evidence(
        category: str,
        claim: str,
        source: str,
        *,
        evidence_type: str,
        subject: str,
        payload: dict[str, Any],
        location: dict[str, Any],
        commit_sha: Any,
        strength_class: str,
        extraction_method: str,
    ):
        nonlocal counter

        evidence.append(
            {
                "id": f"E{counter:03d}",
                "category": category,
                "claim": claim,
                "source": source,
                "evidence_type": evidence_type,
                "subject": subject,
                "payload": payload,
                "location": location,
                "commit_sha": commit_sha,
                "strength_class": strength_class,
                "extraction_method": extraction_method,
            }
        )

        counter += 1

    def add_repository_evidence(field: str, claim: str, value: Any):
        add_evidence(
            "repository",
            claim,
            "GitHub repository metadata",
            evidence_type="repository_metadata",
            subject=f"repository.{field}",
            payload={"field": field, "value": value},
            location={"field": field},
            commit_sha=tree_sha,
            strength_class="observed",
            extraction_method="github_repos_api",
        )

    # ---------------------------------------------------------
    # REPOSITORY METADATA
    # ---------------------------------------------------------

    repository = github_data.get("repository", {})

    if repository:

        if repository.get("name") is not None:
            add_repository_evidence(
                "name",
                f"Repository name is '{repository['name']}'.",
                repository["name"],
            )

        if repository.get("full_name") is not None:
            add_repository_evidence(
                "full_name",
                f"Repository full name is '{repository['full_name']}'.",
                repository["full_name"],
            )

        if repository.get("description") is not None:
            add_repository_evidence(
                "description",
                f"Repository description is '{repository['description']}'.",
                repository["description"],
            )

        if repository.get("language") is not None:
            add_repository_evidence(
                "language",
                f"Primary repository language is '{repository['language']}'.",
                repository["language"],
            )

        if repository.get("default_branch") is not None:
            add_repository_evidence(
                "default_branch",
                f"Default branch is '{repository['default_branch']}'.",
                repository["default_branch"],
            )

        if repository.get("stars") is not None:
            add_repository_evidence(
                "stars",
                f"Repository has {repository['stars']} star(s).",
                repository["stars"],
            )

        if repository.get("forks") is not None:
            add_repository_evidence(
                "forks",
                f"Repository has {repository['forks']} fork(s).",
                repository["forks"],
            )

        if repository.get("open_issues") is not None:
            add_repository_evidence(
                "open_issues",
                f"Repository has {repository['open_issues']} open issue(s).",
                repository["open_issues"],
            )

        if repository.get("default_branch") is not None:
            add_repository_evidence(
                "default_branch",
                f"Repository default branch is '{repository['default_branch']}'.",
                repository["default_branch"],
            )

        if repository.get("visibility") is not None:
            add_repository_evidence(
                "visibility",
                f"Repository visibility is '{repository['visibility']}'.",
                repository["visibility"],
            )

        if repository.get("archived") is not None:
            add_repository_evidence(
                "archived",
                f"Repository archived status is {repository['archived']}.",
                repository["archived"],
            )

    # ---------------------------------------------------------
    # FILE TREE
    # ---------------------------------------------------------

    for item in file_tree:

        path = item.get("path")
        item_type = item.get("type")

        if not path:
            continue

        item_sha = item.get("sha") or tree_sha

        if item_type == "directory":

            add_evidence(
                "directory",
                f"Repository contains directory '{path}'.",
                "GitHub repository file tree",
                evidence_type="tree_fact",
                subject=path,
                payload={"path": path, "type": "directory"},
                location={"path": path},
                commit_sha=item_sha,
                strength_class="observed",
                extraction_method="github_git_trees",
            )

        elif item_type == "file":

            size = item.get("size", 0)

            add_evidence(
                "file",
                f"Repository contains file '{path}' with size {size} bytes.",
                "GitHub repository file tree",
                evidence_type="tree_fact",
                subject=path,
                payload={"path": path, "type": "file", "size": size},
                location={"path": path},
                commit_sha=item_sha,
                strength_class="observed",
                extraction_method="github_git_trees",
            )

    # ---------------------------------------------------------
    # RETRIEVED SOURCE FILES
    # ---------------------------------------------------------

    important_files = github_data.get("important_files", {})

    for path, content in important_files.items():

        if not path:
            continue

        blob_sha = tree_sha_by_path.get(path) or tree_sha

        if content:

            excerpt = content[:1200]

            add_evidence(
                "source_code",
                (
                    f"Source code for '{path}' was retrieved. "
                    f"Relevant source excerpt:\n{excerpt}"
                ),
                path,
                evidence_type="source_retrieval",
                subject=path,
                payload={"path": path, "retrieved": True},
                location={"path": path},
                commit_sha=blob_sha,
                strength_class="observed",
                extraction_method="github_contents_api",
            )

        else:

            add_evidence(
                "file",
                f"File '{path}' exists, but its contents were not retrieved.",
                path,
                evidence_type="source_retrieval",
                subject=path,
                payload={"path": path, "retrieved": False},
                location={"path": path},
                commit_sha=blob_sha,
                strength_class="observed",
                extraction_method="github_contents_api",
            )

    return evidence
