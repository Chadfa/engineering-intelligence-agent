from app.graph.eia_graph import eia_graph


result = eia_graph.invoke(
    {
        "user_message": (
            "Analyze this GitHub repository: "
            "https://github.com/Chadfa/engineering-intelligence-agent"
        ),
        "response": "",
        "github_data": None,
    }
)

print("\n=== EIA RESPONSE ===\n")
print(result["response"])