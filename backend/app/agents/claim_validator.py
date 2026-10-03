from typing import Any
import re


# Source-derived capability evidence is not produced by the evidence
# builder in this slice, so the allow-set is intentionally empty.
ALLOWED_EVIDENCE_TYPES = {
    "repo_attribute": frozenset({"repository_metadata"}),
    "existence": frozenset({"tree_fact"}),
    "structure": frozenset({"tree_fact", "repository_metadata"}),
    "capability": frozenset(),
    "assessment": frozenset(),
}

_ASSESSMENT_RE = re.compile(
    r"\b("
    r"risk|risky|insecure|unsafe|should|recommend(?:ed|ation)?|"
    r"poor(?:ly)?|quality|maintainability|well[- ]designed|"
    r"likely|probably|appears|seems|infer(?:ence)?|concern|"
    r"technical debt|evaluat(?:e|ion)|assess(?:ment)?|"
    r"vulnerable|judgment|judgement"
    r")\b",
    re.IGNORECASE,
)

_EXISTENCE_RE = re.compile(
    r"contains (?:a |an )?[\w./-]+(?:\s+and\s+[\w./-]+)*\s+files?\b|"
    r"has (?:a |an )?[\w./-]+(?:\s+and\s+[\w./-]+)*\s+files?\b|"
    r"includes (?:a |an )?[\w./-]+(?:\s+and\s+[\w./-]+)*\s+files?\b|"
    r"contains (?:a |an )?directory\b|"
    r"has (?:a |an )?directory\b|"
    r"file exists|directory exists|"
    r"contains file|contains directory",
    re.IGNORECASE,
)

_STRUCTURE_RE = re.compile(
    r"\b("
    r"layout|structure|organized|organised|"
    r"package layout|project structure|directory structure|"
    r"codebase structure|monorepo|\bpackage\b"
    r")\b",
    re.IGNORECASE,
)

_REPO_ATTRIBUTE_RE = re.compile(
    r"written in|primary (?:repository )?language|language is|"
    r"default branch|visibility|archived|"
    r"\bnamed\b|full name|description is|"
    r"\bstars?\b|\bforks?\b|open issues?|"
    r"the repository is (?:public|private)",
    re.IGNORECASE,
)

_CAPABILITY_RE = re.compile(
    r"\b("
    r"uses|using|implements|exposes|configures|configured|"
    r"authentication|authori[sz]ation|provides|enables"
    r")\b",
    re.IGNORECASE,
)


def classify_claim(claim: str) -> str:
    """
    Classify a claim from claim text only.

    Cited evidence IDs and categories are not used.
    Uncertain claims default to capability.
    """

    text = claim or ""

    if _ASSESSMENT_RE.search(text):
        return "assessment"

    if _EXISTENCE_RE.search(text):
        return "existence"

    if _STRUCTURE_RE.search(text):
        return "structure"

    if _REPO_ATTRIBUTE_RE.search(text):
        return "repo_attribute"

    if _CAPABILITY_RE.search(text):
        return "capability"

    return "capability"


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

def _structured_repository_attribute_match(
    claim: str,
    evidence_items: list[dict[str, Any]],
) -> bool:
    """
    Check simple repository attributes against structured evidence.
    """

    claim_text = _normalise(claim)

    checks = []

    language_match = re.search(
        r"written in\s+([a-z0-9+#-]+)",
        claim_text,
    )
    if language_match:
        checks.append(("language", language_match.group(1)))
    
    name_match = re.search(
        r"repository (?:is )?named ['\"]?([a-z0-9_.-]+)",
        claim_text,
    )
    if name_match:
        checks.append(("name", name_match.group(1)))

    if not checks:
        return True

    for field, claimed_value in checks:
        matched = False

        for evidence in evidence_items:
            if evidence.get("evidence_type") != "repository_metadata":
                continue

            payload = evidence.get("payload", {})

            if payload.get("field") != field:
                continue

            actual_value = str(payload.get("value", "")).strip()

            if claimed_value.lower() == actual_value.lower():
                matched = True
                break

        if not matched:
            return False

    return True

def _structured_path_match(
    claim: str,
    evidence_items: list[dict[str, Any]],
) -> bool:
    """
    Check simple file/directory existence claims against tree facts.
    """

    claim_text = _normalise(claim)

    path_match = re.search(
        r"(?:contains|has|includes)\s+(?:a|an)?\s*"
        r"([a-z0-9_./\\-]+)\s+(?:file|directory)\b",
        claim_text,
    )

    if not path_match:
        return True

    claimed_path = path_match.group(1).replace("\\", "/")

    if "/" not in claimed_path:
        return True

    claimed_type = (
        "directory"
        if "directory" in path_match.group(0)
        else "file"
    )

    for evidence in evidence_items:
        if evidence.get("evidence_type") != "tree_fact":
            continue

        payload = evidence.get("payload", {})
        evidence_path = str(payload.get("path", "")).replace("\\", "/")
        evidence_type = payload.get("type")

        if (
            evidence_path == claimed_path
            and evidence_type == claimed_type
        ):
            return True

    return False
   
def _claim_supported_by_evidence(
    claim: str,
    evidence_items: list[dict[str, Any]],
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


def _existence_names(claim: str) -> list[str]:
    """Extract file or directory names from simple existence claims."""

    claim_text = _normalise(claim)

    match = re.search(
        r"(?:contains|has|includes)\s+"
        r"(.+?)\s+(?:file|files|directory|directories)\b",
        claim_text,
    )

    if not match:
        return []

    names_text = match.group(1)

    names = re.split(r"\s+and\s+", names_text)

    names = [
        re.sub(r"^(?:a|an)\s+", "", name).strip()
        for name in names
    ]

    return [
        name.strip(" .,'\"")
        for name in names
        if name.strip(" .,'\"")
    ]


def _subjects_compatible(
    claim: str,
    claim_type: str,
    evidence_items: list[dict[str, Any]],
) -> bool:
    """Conservative subject check used only for existence claims."""

    if claim_type != "existence":
        return True

    names = _existence_names(claim)

    if not names:
        return True

    for name in names:
        needle = name.replace("\\", "/").lower()
        matched = False

        for evidence in evidence_items:
            subject = str(
                evidence.get("subject") or ""
            ).replace("\\", "/")

            payload = evidence.get("payload") or {}

            path = str(
                payload.get("path") or subject
            ).replace("\\", "/")

            normalized_subject = subject.lstrip("./").lower()
            normalized_path = path.lstrip("./").lower()

            if "/" in needle:
                if (
                    normalized_path == needle
                    or normalized_subject == needle
                ):
                    matched = True
                    break
            else:
                if (
                    normalized_path == needle
                    or normalized_subject == needle
                    or normalized_path.rsplit("/", 1)[-1] == needle
                    or normalized_subject.rsplit("/", 1)[-1] == needle
                ):
                    matched = True
                    break

        if not matched:
            return False

    return True


def validate_claims(
    claims: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
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

        claim_type = classify_claim(claim)
        allowed_types = ALLOWED_EVIDENCE_TYPES.get(
            claim_type,
            frozenset(),
        )
        allowed_evidence = [
            evidence_item
            for evidence_item in referenced_evidence
            if evidence_item.get("evidence_type") in allowed_types
        ]
        has_wrong_evidence_type = any(
            evidence_item.get("evidence_type") not in allowed_types
            for evidence_item in referenced_evidence)

        if not valid_ids:

            validation = "unsupported"
            reason = "evidence_missing"

        elif claim_type == "assessment":

            validation = "insufficient_evidence"
            reason = "claim_type_mismatch"

        elif has_wrong_evidence_type:
            validation = "insufficient_evidence"
            reason = "wrong_evidence_type"

        elif not allowed_evidence:

            validation = "insufficient_evidence"
            reason = "wrong_evidence_type"

        elif claim_type == "repo_attribute" and not _structured_repository_attribute_match(
            claim,
            allowed_evidence,
        ):
            validation = "insufficient_evidence"
            reason = "structured_attribute_mismatch"
        elif claim_type == "existence" and not _structured_path_match(
            claim,
            allowed_evidence,
        ):
            validation = "insufficient_evidence"
            reason = "structured_path_mismatch"
        elif not _subjects_compatible(
            claim,
            claim_type,
            allowed_evidence,
        ):
            validation = "insufficient_evidence"
            reason = "subject_mismatch"
        elif not _claim_supported_by_evidence(
            claim,
            allowed_evidence,
        ):
            validation = "insufficient_evidence"
            reason = "legacy_evidence_text_only"
        else:
                validation = "supported"
                reason = None

        validated_claims.append(
            {
                "claim": claim,
                "evidence_ids": valid_ids,
                "validation": validation,
                "reason": reason,
            }
        )

    return validated_claims