import re
import json
import ast

from langchain_ollama import ChatOllama

from app.agents.agent_tools import inspect_github_repository
from app.agents.evidence_validator import parse_and_validate_analysis
from app.agents.evidence_builder import build_evidence
from app.agents.claim_validator import validate_claims                                  


llm = ChatOllama(
    model="qwen2.5:7b",
    temperature=0,
)


SYSTEM_PROMPT = """
You are Engineering Intelligence Agent (EIA).

You are an engineering assistant.

You receive either:

1. A normal engineering question.
2. A user request together with verified GitHub repository evidence.

Rules:

- Never invent repository facts.
- Never invent files.
- Never invent statistics.
- Never claim to have inspected data that was not provided.
- Distinguish verified facts from inference.
- When evidence is provided, use ONLY that evidence.
"""


def extract_github_repository(message: str):
    patterns = [
        r"github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)",
        r"\b([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, message)

        if match:
            owner = match.group(1)
            repo = match.group(2).rstrip(".,!?/")
            return owner, repo

    return None


def run_eia(message: str) -> str:

    repository = extract_github_repository(message)

    # ---------------------------------------------------------
    # GENERAL QUESTION
    # ---------------------------------------------------------

    if repository is None:

        response = llm.invoke(
            [
                ("system", SYSTEM_PROMPT),
                ("human", message),
            ]
        )

        return response.content

    # ---------------------------------------------------------
    # GITHUB REQUEST
    # ---------------------------------------------------------
    owner, repo = repository

    github_result = inspect_github_repository.invoke(
        {
            "owner": owner,
            "repo": repo,
        }
    )

    github_data = ast.literal_eval(github_result)

    evidence = build_evidence(github_data)

    evidence_text = "\n".join(
        f"{item['id']}: {item['claim']} "
        f"(Source: {item['source']})"
        for item in evidence
    )

    analysis_prompt = f"""
You are analyzing a GitHub repository.

USER REQUEST:
{message}

VERIFIED EVIDENCE:

{evidence_text}

Your job is to produce an evidence-grounded engineering analysis.

STRICT RULES:

1. Use ONLY the evidence listed above.
2. Never invent repository facts.
3. Never invent files.
4. Never invent statistics.
5. Never invent technologies.
6. Every factual claim MUST reference one or more evidence IDs.
7. Evidence IDs must come from the evidence list above.
8. Do not create evidence IDs yourself.
9. Do not use a filename as proof of its contents.
10. A source-code claim is allowed only when the corresponding
    file appears as retrieved source-code evidence.
11. Separate verified facts from engineering inferences.
12. If evidence is insufficient, say so.

Return ONLY valid JSON.

Use exactly this structure:

{{
  "summary": "string",
  "claims": [
    {{
      "claim": "string",
      "evidence_ids": ["E001"]
    }}
  ],
  "engineering_inferences": [
    {{
      "claim": "string",
      "evidence_ids": ["E001"]
    }}
  ],
  "risks": [
    {{
      "claim": "string",
      "evidence_ids": ["E001"]
    }}
  ],
  "recommendations": [
    "string"
  ]
}}

IMPORTANT:

Every item in "claims", "engineering_inferences", and "risks"
must contain evidence_ids.

Recommendations do not require evidence IDs because they are
engineering suggestions rather than repository facts.

Do not use Markdown.
Do not add extra fields.
"""

    response = llm.invoke(
        [
            ("system", SYSTEM_PROMPT),
            ("human", analysis_prompt),
        ]
    )

    try:
        analysis = json.loads(response.content)

    except json.JSONDecodeError:

        return json.dumps(
            {
                "summary": "The analysis model returned invalid JSON.",
                "claims": [],
                "engineering_inferences": [],
                "risks": [],
                "recommendations": [],
            },
            indent=2,
            ensure_ascii=False,
        )

    validated_claims = validate_claims(
        analysis.get("claims", []),
        evidence,
    )

    validated_inferences = validate_claims(
        analysis.get("engineering_inferences", []),
        evidence,
    )

    validated_risks = validate_claims(
        analysis.get("risks", []),
        evidence,
    )

    validated = {
        "summary": (
            analysis.get("summary", "")
            if isinstance(analysis.get("summary", ""), str)
            else ""
        ),
        "claims": validated_claims,
        "engineering_inferences": validated_inferences,
        "risks": validated_risks,
        "recommendations": (
            analysis.get("recommendations", [])
            if isinstance(analysis.get("recommendations", []), list)
            else []
        ),
    }

    return json.dumps(
        validated,
        indent=2,
        ensure_ascii=False,
    )