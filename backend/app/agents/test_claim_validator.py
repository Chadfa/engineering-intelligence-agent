from app.agents.claim_validator import validate_claims


if __name__ == "__main__":

    evidence = [
        {
            "id": "E001",
            "category": "repository",
            "claim": "Repository name is 'engineering-intelligence-agent'.",
            "source": "GitHub repository metadata",
        },
        {
            "id": "E002",
            "category": "repository",
            "claim": "Primary repository language is 'Python'.",
            "source": "GitHub repository metadata",
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
    ]

    validated = validate_claims(
        claims,
        evidence,
    )

    print("\n=== CONTENT-AWARE CLAIM VALIDATION ===\n")

    for item in validated:
        print(item)