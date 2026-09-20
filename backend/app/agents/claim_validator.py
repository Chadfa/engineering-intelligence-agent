from typing import Any
import re


def _normalise(text: str) -> str:
    """Convert text into a simple comparable form."""
    return " ".join(text.lower().strip().split())


def _claim_supported_by_evidence(
    claim: str,
    evidence_items: list[dict[str, str]],
) -> bool:
    """
    Perform a conservative deterministic check.

    The validator checks whether the factual value from the evidence
    is present in the claim. This helps distinguish supported claims
    from claims that contain conflicting values.
    """

    claim_text = _normalise(claim)

    for evidence in evidence_items:

        evidence_text = _normalise(
            evidence.get("claim", "")
        )

        if not evidence_text:
            continue

        # -----------------------------------------------------
        # Extract quoted values from evidence.
        #
        # Example:
        # "Primary repository language is 'Python'."
        #                    -> "python"
        # -----------------------------------------------------

        parts = evidence_text.split("'")

        if len(parts) >= 3:

            quoted_values = [
                parts[index].strip()
                for index in range(1, len(parts), 2)
                if parts[index].strip()
            ]

            for value in quoted_values:

                if value in claim_text:
                    return True

        # -----------------------------------------------------
        # Check numeric factual values.
        #
        # Example:
        # "Repository has 0 stars."
        #
        # The claim must contain "0", not "12".
        # -----------------------------------------------------

        evidence_numbers = re.findall(
            r"\b\d+\b",
            evidence_text,
        )

        if evidence_numbers:

            claim_numbers = re.findall(
                r"\b\d+\b",
                claim_text,
            )

            if any(
                number in claim_numbers
                for number in evidence_numbers
            ):
                return True

            # Evidence contains a number but the claim contains
            # a different number.
            continue

        # -----------------------------------------------------
        # Handle file/path evidence.
        #
        # Example evidence:
        # "Repository contains file 'backend/requirements.txt'."
        #
        # Claim:
        # "The repository contains a 'requirements.txt' file."
        # -----------------------------------------------------

        evidence_paths = re.findall(
            r"'([^']+)'",
            evidence_text,
        )

        for path in evidence_paths:

            path = path.strip()

            # Normalize Windows-style paths.
            normalized_path = path.replace("\\", "/")

            # Match the complete path.
            if normalized_path in claim_text:
                return True

            # Match only the filename.
            #
            # Example:
            # backend/requirements.txt
            # -> requirements.txt
            filename = normalized_path.split("/")[-1]

            if filename in claim_text:
                return True

        # -----------------------------------------------------
        # Handle important unquoted factual terms.
        # -----------------------------------------------------

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
                "exists",
            }
        ]

        if meaningful_words:

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