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
        if item["category"] != "source_code"

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

Recommendations do not require evidence IDs, but they MUST be

derived from verified evidence or clearly identified engineering gaps.

Recommendation rules:

1. Do not recommend something that the evidence already shows exists.

2. Do not make generic recommendations unrelated to the repository.

3. Do not recommend adding, fixing, or changing a component unless

   the evidence indicates a relevant gap, limitation, or risk.

4. Prefer recommendations that improve engineering quality,

   maintainability, testing, documentation, security, or reliability

   when the evidence supports such a need.

5. If the available evidence does not reveal a clear engineering gap,

   return an empty recommendations list rather than inventing one.

6. Do not treat repository popularity metrics such as stars or forks

   as proof that the project needs more maintenance, users, or engagement.

Do not use Markdown.
"""

    response = llm.invoke(
        [
            ("system", SYSTEM_PROMPT),
            ("human", analysis_prompt),
        ]
    )


    try:
        raw_output = response.content.strip()

        if raw_output.startswith("```json"):
            raw_output = raw_output[7:]

        if raw_output.endswith("```"):
            raw_output = raw_output[:-3]

        raw_output = raw_output.strip()

        analysis = json.loads(raw_output)

    except json.JSONDecodeError:
        return {
            "summary": "The analysis model returned invalid JSON.",
            "claims": [],
            "engineering_inferences": [],
            "risks": [],
            "recommendations": [],
        }

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
