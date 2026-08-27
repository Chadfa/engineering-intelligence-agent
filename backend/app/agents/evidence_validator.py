import json


def validate_analysis(analysis: dict, evidence: str) -> dict:
    """
    Basic validation layer for EIA analysis.

    The LLM is responsible for reasoning.
    This layer makes sure the expected response structure exists
    and removes empty/invalid fields.
    """

    required_fields = [
        "summary",
        "verified_facts",
        "technology_observations",
        "engineering_inferences",
        "risks",
        "recommendations",
    ]

    validated = {}

    for field in required_fields:
        value = analysis.get(field)

        if field == "summary":
            validated[field] = value if isinstance(value, str) else ""

        else:
            if isinstance(value, list):
                validated[field] = [
                    item
                    for item in value
                    if isinstance(item, str) and item.strip()
                ]
            else:
                validated[field] = []

    return validated


def parse_and_validate_analysis(
    model_output: str,
    evidence: str,
) -> dict:
    """
    Parse JSON returned by the LLM and validate its structure.
    """

    try:
        analysis = json.loads(model_output)
    except json.JSONDecodeError:
        return {
            "summary": "The analysis model returned invalid JSON.",
            "verified_facts": [],
            "technology_observations": [],
            "engineering_inferences": [],
            "risks": [],
            "recommendations": [],
        }

    return validate_analysis(
        analysis,
        evidence,
    )