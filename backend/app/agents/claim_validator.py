from typing import Any
import re


def _normalise(text: str) -> str:
    """Convert text into a simple comparable form."""
    return " ".join(text.lower().strip().split())


def _split_claim(claim: str) -> list[str]:
    """Split simple compound claims into smaller factual statements."""
    parts = re.split(r"\s+and\s+", claim, flags=re.IGNORECASE)

    return [
        part.strip(" .")
        for part in parts
        if part.strip(" .")
    ]


def _claim_supported_by_evidence(
    claim: str,
    evidence_items: list[dict[str, str]],
) -> bool:
    """
    Perform a conservative deterministic check.
    """

    claim_text = _normalise(claim)

    claim_parts = [
        _normalise(part)
        for part in _split_claim(claim)
    ]

    for evidence in evidence_items:

        evidence_text = _normalise(
            evidence.get("claim", "")
        )

        if not evidence_text:
            continue

        # -----------------------------------------------------
        # Extract quoted values from evidence.
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
        # Handle file/path evidence.
        # -----------------------------------------------------

        evidence_paths = re.findall(
            r"'([^']+)'",
            evidence_text,
        )

        for path in evidence_paths:

            path = path.strip()

            normalized_path = path.replace("\\", "/")

            # Match complete path.
            if normalized_path in claim_text:
                return True

            # Match filename.
            evidence_filename = normalized_path.split("/")[-1].strip()

            if evidence_filename in claim_text:
                return True

            # Match filename without extension.
            #
            # Example:
            # README -> README.md
            #
            evidence_stem = evidence_filename.rsplit(
                ".",
                1,
            )[0]

            if evidence_stem in claim_text:
                return True

        # -----------------------------------------------------
        # Handle simple file-existence claims.
        # -----------------------------------------------------

        file_existence_patterns = [
            r"contains (?:a|an)?\s*([.\w-]+)\s+file",
            r"has (?:a|an)?\s*([.\w-]+)\s+file",
            r"includes (?:a|an)?\s*([.\w-]+)\s+file",
        ]

        for pattern in file_existence_patterns:

            matches = re.findall(
                pattern,
                claim_text,
            )

            for filename in matches:

                filename = filename.strip(" .")

                for path in evidence_paths:

                    evidence_filename = (
                        path.replace("\\", "/")
                        .split("/")[-1]
                        .strip()
                    )

                    if filename == evidence_filename:
                        return True

                    evidence_stem = evidence_filename.rsplit(
                        ".",
                        1,
                    )[0]

                    if filename == evidence_stem:
                        return True

        # -----------------------------------------------------
        # Check numeric factual values.
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

            continue

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