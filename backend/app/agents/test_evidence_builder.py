import ast

from app.agents.agent_tools import inspect_github_repository
from app.agents.evidence_builder import build_evidence


REQUIRED_FIELDS = (
    "id",
    "category",
    "claim",
    "source",
    "evidence_type",
    "subject",
    "payload",
    "location",
    "commit_sha",
    "strength_class",
    "extraction_method",
)


def _fail(message: str):
    raise SystemExit(f"FAIL: {message}")


def _assert(condition: bool, message: str):
    if not condition:
        _fail(message)


def check_evidence_item(item: dict, index: int):
    for field in REQUIRED_FIELDS:
        _assert(
            field in item,
            f"item {index} missing field {field!r}",
        )

    _assert(isinstance(item["id"], str), f"item {index} id is not a str")
    _assert(isinstance(item["category"], str), f"item {index} category is not a str")
    _assert(isinstance(item["claim"], str), f"item {index} claim is not a str")
    _assert(isinstance(item["source"], str), f"item {index} source is not a str")
    _assert(
        isinstance(item["evidence_type"], str),
        f"item {index} evidence_type is not a str",
    )
    _assert(isinstance(item["subject"], str), f"item {index} subject is not a str")
    _assert(isinstance(item["payload"], dict), f"item {index} payload is not a dict")
    _assert(isinstance(item["location"], dict), f"item {index} location is not a dict")
    _assert(
        item["commit_sha"] is None or isinstance(item["commit_sha"], str),
        f"item {index} commit_sha must be str or None",
    )
    _assert(
        isinstance(item["strength_class"], str),
        f"item {index} strength_class is not a str",
    )
    _assert(
        isinstance(item["extraction_method"], str),
        f"item {index} extraction_method is not a str",
    )


def check_synthetic_evidence():
    github_data = {
        "tree_sha": "abc123tree",
        "truncated": False,
        "repository": {
            "name": "engineering-intelligence-agent",
            "full_name": "Chadfa/engineering-intelligence-agent",
            "description": None,
            "language": "Python",
            "stars": 0,
            "forks": 0,
            "open_issues": 1,
            "default_branch": "main",
            "visibility": "public",
            "archived": False,
        },
        "file_tree": [
            {
                "path": "backend",
                "type": "directory",
                "sha": "dirsha1",
            },
            {
                "path": "README.md",
                "type": "file",
                "size": 42,
                "sha": "blobsha1",
            },
        ],
        "important_files": {
            "README.md": "# Hello",
            "missing.txt": "",
        },
    }

    evidence = build_evidence(github_data)

    _assert(evidence, "synthetic evidence is empty")
    _assert(
        evidence[0]["id"] == "E001",
        f"expected first id E001, got {evidence[0]['id']!r}",
    )

    for index, item in enumerate(evidence):
        check_evidence_item(item, index)

    name_item = evidence[0]
    _assert(
        name_item["claim"]
        == "Repository name is 'engineering-intelligence-agent'.",
        "repository name claim text changed",
    )
    _assert(name_item["category"] == "repository", "repository category changed")
    _assert(
        name_item["source"] == "GitHub repository metadata",
        "repository source changed",
    )
    _assert(name_item["evidence_type"] == "repository_metadata", "name evidence_type")
    _assert(name_item["subject"] == "repository.name", "name subject")
    _assert(
        name_item["payload"]
        == {"field": "name", "value": "engineering-intelligence-agent"},
        "name payload",
    )
    _assert(name_item["location"] == {"field": "name"}, "name location")
    _assert(name_item["commit_sha"] == "abc123tree", "name commit_sha")
    _assert(name_item["strength_class"] == "observed", "name strength_class")
    _assert(
        name_item["extraction_method"] == "github_repos_api",
        "name extraction_method",
    )

    directory_items = [
        item for item in evidence if item["evidence_type"] == "tree_fact"
        and item["payload"].get("type") == "directory"
    ]
    file_items = [
        item for item in evidence if item["evidence_type"] == "tree_fact"
        and item["payload"].get("type") == "file"
    ]
    retrieved_items = [
        item for item in evidence if item["evidence_type"] == "source_retrieval"
        and item["payload"].get("retrieved") is True
    ]
    missing_items = [
        item for item in evidence if item["evidence_type"] == "source_retrieval"
        and item["payload"].get("retrieved") is False
    ]

    _assert(len(directory_items) == 1, "expected one directory tree_fact")
    _assert(
        directory_items[0]["claim"]
        == "Repository contains directory 'backend'.",
        "directory claim text changed",
    )
    _assert(directory_items[0]["category"] == "directory", "directory category")
    _assert(
        directory_items[0]["source"] == "GitHub repository file tree",
        "directory source",
    )
    _assert(directory_items[0]["subject"] == "backend", "directory subject")
    _assert(
        directory_items[0]["payload"]
        == {"path": "backend", "type": "directory"},
        "directory payload",
    )
    _assert(directory_items[0]["location"] == {"path": "backend"}, "directory location")
    _assert(directory_items[0]["commit_sha"] == "dirsha1", "directory commit_sha")
    _assert(
        directory_items[0]["extraction_method"] == "github_git_trees",
        "directory extraction_method",
    )

    _assert(len(file_items) == 1, "expected one file tree_fact")
    _assert(
        file_items[0]["claim"]
        == "Repository contains file 'README.md' with size 42 bytes.",
        "file claim text changed",
    )
    _assert(
        file_items[0]["payload"]
        == {"path": "README.md", "type": "file", "size": 42},
        "file payload",
    )
    _assert(file_items[0]["commit_sha"] == "blobsha1", "file commit_sha")

    _assert(len(retrieved_items) == 1, "expected one retrieved source item")
    _assert(
        retrieved_items[0]["claim"].startswith(
            "Source code for 'README.md' was retrieved."
        ),
        "source retrieval claim text changed",
    )
    _assert(retrieved_items[0]["category"] == "source_code", "source category")
    _assert(retrieved_items[0]["source"] == "README.md", "source field")
    _assert(
        retrieved_items[0]["payload"] == {"path": "README.md", "retrieved": True},
        "retrieved payload",
    )
    _assert(retrieved_items[0]["commit_sha"] == "blobsha1", "retrieved commit_sha")
    _assert(
        retrieved_items[0]["extraction_method"] == "github_contents_api",
        "retrieved extraction_method",
    )

    _assert(len(missing_items) == 1, "expected one missing source item")
    _assert(
        missing_items[0]["claim"]
        == "File 'missing.txt' exists, but its contents were not retrieved.",
        "missing file claim text changed",
    )
    _assert(missing_items[0]["category"] == "file", "missing file category")
    _assert(
        missing_items[0]["payload"] == {"path": "missing.txt", "retrieved": False},
        "missing payload",
    )

    empty_tree_evidence = build_evidence(
        {
            "repository": {},
            "file_tree": [],
            "important_files": {},
        }
    )
    _assert(
        empty_tree_evidence == [],
        "empty file tree should not raise and should yield no evidence",
    )

    print("PASS: synthetic evidence metadata checks")


if __name__ == "__main__":

    check_synthetic_evidence()

    github_result = inspect_github_repository.invoke(
        {
            "owner": "Chadfa",
            "repo": "engineering-intelligence-agent",
        }
    )

    github_data = ast.literal_eval(github_result)

    evidence = build_evidence(github_data)

    print("\n=== EVIDENCE ===\n")

    def safe_print(text: str) -> None:
        try:
            print(text)
        except UnicodeEncodeError:
            print(text.encode("ascii", "replace").decode("ascii"))

    for index, item in enumerate(evidence):
        check_evidence_item(item, index)
        safe_print(
            f"{item['id']} | "
            f"{item['category']} | "
            f"{item['evidence_type']} | "
            f"{item['subject']} | "
            f"{item['claim']} | "
            f"Source: {item['source']} | "
            f"SHA: {item['commit_sha']} | "
            f"payload={item['payload']} | "
            f"location={item['location']} | "
            f"{item['strength_class']} | "
            f"{item['extraction_method']}"
        )

    print("\nPASS: live evidence metadata checks")
