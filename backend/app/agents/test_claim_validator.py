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

    settings_evidence = {
        "id": "E003",
        "category": "file",
        "claim": "Repository contains file 'settings.py' with size 366 bytes.",
        "source": "GitHub repository file tree",
        "evidence_type": "tree_fact",
        "subject": "settings.py",
        "payload": {
            "path": "settings.py",
            "type": "file",
            "size": 366,
        },
        "location": {"path": "settings.py"},
        "commit_sha": "blobsha1",
        "strength_class": "observed",
        "extraction_method": "github_git_trees",
    }
    backend_evidence = {
        "id": "E004",
        "category": "directory",
        "claim": "Repository contains directory 'backend'.",
        "source": "GitHub repository file tree",
        "evidence_type": "tree_fact",
        "subject": "backend",
        "payload": {
            "path": "backend",
            "type": "directory",
        },
        "location": {"path": "backend"},
        "commit_sha": "dirsha1",
        "strength_class": "observed",
        "extraction_method": "github_git_trees",
    }
    jwt_file_evidence = {
        "id": "E005",
        "category": "file",
        "claim": "Repository contains file 'jwt.py' with size 120 bytes.",
        "source": "GitHub repository file tree",
        "evidence_type": "tree_fact",
        "subject": "jwt.py",
        "payload": {
            "path": "jwt.py",
            "type": "file",
            "size": 120,
        },
        "location": {"path": "jwt.py"},
        "commit_sha": "blobsha2",
        "strength_class": "observed",
        "extraction_method": "github_git_trees",
    }

    fastapi_evidence = {
        "id": "E006",
        "category": "technology",
        "claim": "Source file 'backend/main.py' explicitly imports technology 'FastAPI'.",
        "source": "backend/main.py",
        "evidence_type": "technology",
        "subject": "FastAPI",
        "payload": {
            "technology": "FastAPI",
            "source_path": "backend/main.py",
        },
        "location": {"path": "backend/main.py"},
        "commit_sha": "blobsha3",
        "strength_class": "observed",
        "extraction_method": "python_ast_imports",
    }
    django_evidence = {
        "id": "E007",
        "category": "technology",
        "claim": "Source file 'backend/django_app.py' explicitly imports technology 'Django'.",
        "source": "backend/django_app.py",
        "evidence_type": "technology",
        "subject": "Django",
        "payload": {
            "technology": "Django",
            "source_path": "backend/django_app.py",
        },
        "location": {"path": "backend/django_app.py"},
        "commit_sha": "blobsha4",
        "strength_class": "observed",
        "extraction_method": "python_ast_imports",
    }

    step8b_evidence = evidence + [
        settings_evidence,
        backend_evidence,
        jwt_file_evidence,
        fastapi_evidence,
        django_evidence,
    ]

    step8b_cases = [
        {
            "name": "repo_attribute + repository_metadata + Python",
            "claims": [
                {
                    "claim": "The repository is written in Python.",
                    "evidence_ids": ["E002"],
                }
            ],
            "expected_validation": "supported",
            "expected_reason": None,
        },
        {
            "name": "capability + tree_fact + JWT",
            "claims": [
                {
                    "claim": "The repository uses JWT authentication.",
                    "evidence_ids": ["E003"],
                }
            ],
            "expected_validation": "insufficient_evidence",
            "expected_reason": "wrong_evidence_type",
        },
        {
            "name": "existence + tree_fact + settings.py",
            "claims": [
                {
                    "claim": "The repository contains a settings.py file.",
                    "evidence_ids": ["E003"],
                }
            ],
            "expected_validation": "supported",
            "expected_reason": None,
        },
        {
            "name": "existence + tree_fact + wrong filename",
            "claims": [
                {
                    "claim": "The repository contains a config.py file.",
                    "evidence_ids": ["E003"],
                }
            ],
            "expected_validation": "insufficient_evidence",
            "expected_reason": "subject_mismatch",
        },
        {
            "name": "existence + tree_fact + partial path",
            "claims": [
                {
                    "claim": "The repository contains backend/settings.py file.",
                    "evidence_ids": ["E003"],
                }
            ],
            "expected_validation": "insufficient_evidence",
            "expected_reason": "structured_path_mismatch",
        },
        {
            "name": "existence + tree_fact + wrong type",
            "claims": [
                {
                    "claim": "The repository contains a settings.py directory.",
                    "evidence_ids": ["E003"],
                }
            ],
            "expected_validation": "insufficient_evidence",
            "expected_reason": "wrong_evidence_type",
        },
        {
            "name": "existence + compound paths with missing entity",
            "claims": [
                {
                    "claim": "The repository contains settings.py and app.py files.",
                    "evidence_ids": ["E003"],
                }
            ],
            "expected_validation": "insufficient_evidence",
            "expected_reason": "subject_mismatch",
        },
        {
            "name": "structure + tree_fact",
            "claims": [
                {
                    "claim": "The repository is organized with a backend directory.",
                    "evidence_ids": ["E004"],
                }
            ],
            "expected_validation": "supported",
            "expected_reason": None,
        },
        {
            "name": "capability + repository_metadata",
            "claims": [
                {
                    "claim": "The repository uses FastAPI.",
                    "evidence_ids": ["E002"],
                }
            ],
            "expected_validation": "insufficient_evidence",
            "expected_reason": "wrong_evidence_type",
        },
        {
            "name": "capability + technology + FastAPI",
            "claims": [
                {
                    "claim": "The repository uses FastAPI.",
                    "evidence_ids": ["E006"],
                }
            ],
            "expected_validation": "supported",
            "expected_reason": None,
        },
        {
            "name": "capability + technology + wrong library",
            "claims": [
                {
                    "claim": "The repository uses Django.",
                    "evidence_ids": ["E006"],
                }
            ],
            "expected_validation": "insufficient_evidence",
            "expected_reason": "structured_technology_mismatch",
        },
        {
            "name": "compound technology claim with missing library",
            "claims": [
                {
                    "claim": "The repository uses FastAPI and Django.",
                    "evidence_ids": ["E006"],
                }
            ],
            "expected_validation": "insufficient_evidence",
            "expected_reason": "structured_technology_mismatch",
        },
        {
            "name": "compound technology claim with both libraries",
            "claims": [
                {
                    "claim": "The repository uses FastAPI and Django.",
                    "evidence_ids": ["E006", "E007"],
                }
            ],
            "expected_validation": "supported",
            "expected_reason": None,
        },
        {
            "name": "assessment",
            "claims": [
                {
                    "claim": "The repository has poor maintainability.",
                    "evidence_ids": ["E001"],
                }
            ],
            "expected_validation": "insufficient_evidence",
            "expected_reason": "claim_type_mismatch",
        },
        {
            "name": "invalid evidence ID",
            "claims": [
                {
                    "claim": "The repository is public.",
                    "evidence_ids": ["E999"],
                }
            ],
            "expected_validation": "unsupported",
            "expected_reason": "evidence_missing",
        },
        {
            "name": "tree_fact filename overlap cannot support capability",
            "claims": [
                {
                    "claim": "The repository uses JWT authentication.",
                    "evidence_ids": ["E005"],
                }
            ],
            "expected_validation": "insufficient_evidence",
            "expected_reason": "wrong_evidence_type",
        },
        {
            "name": "compound existence + capability cannot be supported by tree_fact",
            "claims": [
                {
                    "claim": "The repository contains jwt.py and uses JWT authentication.",
                    "evidence_ids": ["E005"],
                }
            ],
            "expected_validation": "insufficient_evidence",
            "expected_reason": "wrong_evidence_type",
        },
    ]

    print("\n=== STEP 8B CLAIM GATE ===\n")

    for case in step8b_cases:
        results = validate_claims(
            case["claims"],
            step8b_evidence,
        )

        if len(results) != 1:
            raise SystemExit(
                f"FAIL: {case['name']} expected 1 result, got {results}"
            )

        result = results[0]
        print(f"{case['name']}: {result}")

        if result["validation"] != case["expected_validation"]:
            raise SystemExit(
                f"FAIL: {case['name']} expected "
                f"{case['expected_validation']}, got {result['validation']}"
            )

        if result.get("reason") != case["expected_reason"]:
            raise SystemExit(
                f"FAIL: {case['name']} expected reason "
                f"{case['expected_reason']!r}, got {result.get('reason')!r}"
            )

        if "validation" not in result:
            raise SystemExit(
                f"FAIL: {case['name']} missing validation status"
            )

    # The legacy text matcher would accept jwt.py -> "JWT" overlap.
    overlap_text_match = validate_claims(
        [
            {
                "claim": "The repository uses JWT authentication.",
                "evidence_ids": ["E005"],
            }
        ],
        step8b_evidence,
    )[0]

    if overlap_text_match["validation"] == "supported":
        raise SystemExit(
            "FAIL: filename string overlap must not support a capability claim"
        )

    print("\nPASS: step 8B classifier and evidence-type gate")
