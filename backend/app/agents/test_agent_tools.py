from app.agents.agent_tools import inspect_github_repository


if __name__ == "__main__":
    result = inspect_github_repository.invoke(
        {
            "owner": "Chadfa",
            "repo": "engineering-intelligence-agent",
        }
    )

    print("\n=== GITHUB TOOL RESULT ===\n")
    print(result)