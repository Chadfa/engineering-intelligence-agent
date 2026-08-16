from app.graph.eia_graph import eia_graph


result = eia_graph.invoke(
    {
        "user_message": "Explain what a Python virtual environment is.",
        "response": "",
    }
)

print("\n=== EIA RESPONSE ===\n")
print(result["response"])