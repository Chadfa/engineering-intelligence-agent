from app.agents.claim_validator import validate_claims


if __name__ == "__main__":

    evidence = [
        {
            "id": "E001",
            "category": "repository",
            "claim": "Repository name is 'engineering-intelligence-agent'.",
            "source": "GitHub repository metadata",
            "evidence_type": "repository_metadata",
            "subject": "repository.name",
            "payload": {
                "field": "name",
                "value": "engineering-intelligence-agent",
            },
            "location": {"field": "name"},
            "commit_sha": "abc123tree",
            "strength_class": "observed",
            "extraction_method": "github_repos_api",
        },
        {
            "id": "E002",
            "category": "repository",
            "claim": "Primary repository language is 'Python'.",
            "source": "GitHub repository metadata",
            "evidence_type": "repository_metadata",
            "subject": "repository.language",
            "payload": {
                "field": "language",
                "value": "Python",
            },
            "location": {"field": "language"},
            "commit_sha": "abc123tree",
            "strength_class": "observed",
            "extraction_method": "github_repos_api",
        },
    ]

    claims = [
    {
        "claim": "The repository is named 'engineering-intelligence-agent'.",
        "evidence_ids": ["E001"],
    },
    {
        "claim": "The repository uses Java.",
        "evidence_ids": ["E002"],
    },
    {
        "claim": "The repository is written in Python.",
        "evidence_ids": ["E002"],
    },
    {
        "claim": "The repository is public.",
        "evidence_ids": ["E999"],
    },
    {
        "claim": "The repository is named 'engineering-intelligence-agent' and is written in Python.",
        "evidence_ids": ["E001", "E002"],
    },
]

    validated = validate_claims(
        claims,
        evidence,
    )

    print("\n=== CONTENT-AWARE CLAIM VALIDATION ===\n")

    for item in validated:
        print(item)

    expected = [
        "supported",
        "insufficient_evidence",
        "supported",
        "unsupported",
        "supported",
    ]

    actual = [item["validation"] for item in validated]

    if actual != expected:
        raise SystemExit(
            f"FAIL: expected validation {expected}, got {actual}"
        )

    for item in evidence:
        for field in (
            "evidence_type",
            "subject",
            "payload",
            "location",
            "commit_sha",
            "strength_class",
            "extraction_method",
        ):
            if field not in item:
                raise SystemExit(
                    f"FAIL: evidence {item['id']} missing {field}"
                )

        if not isinstance(item["payload"], dict):
            raise SystemExit(
                f"FAIL: evidence {item['id']} payload is not a dict"
            )

        if not isinstance(item["location"], dict):
            raise SystemExit(
                f"FAIL: evidence {item['id']} location is not a dict"
            )

    print("\nPASS: claim validation results and evidence metadata checks")
