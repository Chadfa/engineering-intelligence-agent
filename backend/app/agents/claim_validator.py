from typing import Any


def _normalise(text: str) -> str:
    """Convert text into a simple comparable form."""
    return " ".join(text.lower().strip().split())


def _claim_supported_by_evidence(
    claim: str,
    evidence_items: list[dict[str, str]],
) -> bool:
    """
    Perform a conservative deterministic check.

    The validator looks for important factual terms from the evidence
    inside the claim rather than requiring the complete evidence sentence
    to be repeated.
    """

    claim_text = _normalise(claim)

    for evidence in evidence_items:

        evidence_text = _normalise(
            evidence.get("claim", "")
        )

        if not evidence_text:
            continue

        evidence_words = [
            word.strip(".,'\"()[]{}:")
            for word in evidence_text.split()
        ]

        meaningful_words = [
            word
            for word in evidence_words
            if len(word) >= 4
            and word not in {
                "repository",
                "primary",
                "language",
                "name",
                "full",
                "description",
                "default",
                "branch",
                "contains",
                "directory",
                "file",
                "source",
                "content",
                "retrieved",
                "project",
                "status",
                "archived",
                "visibility",
            }
        ]

        if not meaningful_words:
            continue

        matches = sum(
            1
            for word in meaningful_words
            if word in claim_text
        )

        if matches >= 1:
            return True

    return False


def validate_claims(
    claims: list[dict[str, Any]],
    evidence: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """
    Validate claims against referenced evidence IDs and
    evidence content.
    """

    evidence_map = {
        item["id"]: item
        for item in evidence
    }

    validated_claims = []

    for item in claims:

        if not isinstance(item, dict):
            continue

        claim = item.get("claim")
        evidence_ids = item.get("evidence_ids")

        if not isinstance(claim, str) or not claim.strip():
            continue

        if not isinstance(evidence_ids, list):
            evidence_ids = []

        valid_ids = [
            evidence_id
            for evidence_id in evidence_ids
            if isinstance(evidence_id, str)
            and evidence_id in evidence_map
        ]

        referenced_evidence = [
            evidence_map[evidence_id]
            for evidence_id in valid_ids
        ]

        if not valid_ids:
            validation = "unsupported"

        elif _claim_supported_by_evidence(
            claim,
            referenced_evidence,
        ):
            validation = "supported"

        else:
            validation = "insufficient_evidence"

        validated_claims.append(
            {
                "claim": claim,
                "evidence_ids": valid_ids,
                "validation": validation,
            }
        )

    return validated_claims