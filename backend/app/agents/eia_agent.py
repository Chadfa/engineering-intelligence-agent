import re
import json

from langchain_ollama import ChatOllama

from app.agents.agent_tools import inspect_github_repository
from app.agents.evidence_validator import parse_and_validate_analysis


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

    analysis_prompt = f"""
You are analyzing a GitHub repository.

USER REQUEST:
{message}

VERIFIED GITHUB EVIDENCE:
{github_result}

Analyze the repository using ONLY the verified evidence above.

STRICT RULES:

1. Treat the GitHub evidence as authoritative.
2. Never invent numbers.
3. Never invent files or directories.
4. Never invent technologies.
5. Never claim a file exists unless it appears in the evidence.
6. Never claim a file's contents unless its contents appear in
   the evidence.
7. Do not confuse dependencies with actual usage.
8. Separate verified facts from inference.
9. If evidence is missing, explicitly say that the evidence was not
   retrieved.

Return ONLY valid JSON in this exact shape:

{{
  "summary": "string",
  "verified_facts": [
    "string"
  ],
  "technology_observations": [
    "string"
  ],
  "engineering_inferences": [
    "string"
  ],
  "risks": [
    "string"
  ],
  "recommendations": [
    "string"
  ]
}}

Do not use Markdown.
Do not add fields.
Do not invent evidence.
"""

    response = llm.invoke(
        [
            ("system", SYSTEM_PROMPT),
            ("human", analysis_prompt),
        ]
    )

    validated = parse_and_validate_analysis(
        response.content,
        github_result,
    )

    return json.dumps(
        validated,
        indent=2,
        ensure_ascii=False,
    )