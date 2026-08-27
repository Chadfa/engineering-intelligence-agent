from app.agents.eia_agent import run_eia


if __name__ == "__main__":

    print("\n=== TEST 1: GENERAL QUESTION ===\n")

    response = run_eia(
        "What is the difference between FastAPI and Flask?"
    )

    print(response)

    print("\n=== TEST 2: GITHUB TOOL ===\n")

    response = run_eia(
        "Analyze the GitHub repository "
        "Chadfa/engineering-intelligence-agent. "
        "Give me a short architecture summary."
    )

    print(response)