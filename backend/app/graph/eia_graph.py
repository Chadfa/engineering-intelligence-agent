import re

from langgraph.graph import END, START, StateGraph

from app.agents.eia_agent import run_eia
from app.graph.router import route_request
from app.graph.state import EIAState
from app.tools.github_tool import inspect_repository


def eia_node(state: EIAState) -> EIAState:
    response = run_eia(state["user_message"])

    return {
        **state,
        "response": response,
    }


def github_node(state: EIAState) -> EIAState:
    message = state["user_message"]

    match = re.search(
        r"github\.com/([^/\s]+)/([^/\s]+)",
        message,
    )

    if not match:
        return {
            **state,
            "response": (
                "I couldn't identify a GitHub repository in your request."
            ),
        }

    owner = match.group(1)
    repo = match.group(2).rstrip(".,)")

    github_data = inspect_repository(
        owner,
        repo,
    )

    return {
        **state,
        "github_data": github_data,
    }


def github_analysis_node(state: EIAState) -> EIAState:
    github_data = state.get("github_data")

    prompt = f"""
You are Engineering Intelligence Agent.

Analyze the GitHub repository information below.

Repository data:
{github_data}

User request:
{state["user_message"]}

Provide a useful engineering analysis.

Focus on:
- repository overview
- technology/language
- project structure
- notable files
- likely purpose
- useful observations
- recommended next steps

Do not claim to have analyzed source code that was not provided.
"""

    response = run_eia(prompt)

    return {
        **state,
        "response": response,
    }


builder = StateGraph(EIAState)

builder.add_node("eia", eia_node)
builder.add_node("github", github_node)
builder.add_node("github_analysis", github_analysis_node)

builder.add_conditional_edges(
    START,
    route_request,
    {
        "github": "github",
        "eia": "eia",
    },
)

builder.add_edge("github", "github_analysis")
builder.add_edge("github_analysis", END)
builder.add_edge("eia", END)

eia_graph = builder.compile()