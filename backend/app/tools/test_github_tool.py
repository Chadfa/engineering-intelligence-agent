from pprint import pprint

from app.tools.github_tool import inspect_repository


result = inspect_repository(
    "Chadfa",
    "engineering-intelligence-agent",
)

pprint(result)