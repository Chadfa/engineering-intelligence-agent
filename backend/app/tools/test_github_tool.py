from app.tools.github_tool import inspect_repository


result = inspect_repository(
    "Chadfa",
    "engineering-intelligence-agent",
)

print("\n=== REPOSITORY ===\n")
print(result["repository"])

print("\n=== FILE TREE ===\n")

for item in result["file_tree"]:
    print(item)

print("\n=== IMPORTANT FILES ===\n")

for path, content in result["important_files"].items():
    print(f"\n--- {path} ---")
    print(content[:1000])