import ast

from app.agents.agent_tools import inspect_github_repository
from app.agents.evidence_builder import build_evidence


if __name__ == "__main__":

    github_result = inspect_github_repository.invoke(
        {
            "owner": "Chadfa",
            "repo": "engineering-intelligence-agent",
        }
    )

    github_data = ast.literal_eval(github_result)

    evidence = build_evidence(github_data)

    print("\n=== EVIDENCE ===\n")

    for item in evidence:
        print(
            f"{item['id']} | "
            f"{item['category']} | "
            f"{item['claim']} | "
            f"Source: {item['source']}"
        )