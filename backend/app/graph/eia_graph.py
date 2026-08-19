import json
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

    if not github_data:
        return {
            **state,
            "response": "No GitHub repository data was retrieved.",
        }

    repository = github_data["repository"]
    file_tree = github_data["file_tree"]
    important_files = github_data["important_files"]

    evidence = {
        "repository": repository,
        "directories": [
            item["path"]
            for item in file_tree
            if item["type"] == "directory"
        ],
        "files": [
            {
                "path": item["path"],
                "size": item.get("size", 0),
            }
            for item in file_tree
            if item["type"] == "file"
        ],
        "file_contents": important_files,
    }

    evidence_json = json.dumps(
        evidence,
        indent=2,
        ensure_ascii=False,
    )

    prompt = f"""
You are Engineering Intelligence Agent.

Analyze ONLY the verified GitHub evidence below.

DO NOT invent facts.
DO NOT infer files that are not listed.
DO NOT invent statistics.
DO NOT invent directories.
DO NOT invent technologies.

IMPORTANT:

A filename alone does NOT prove what a file does.

A Python import alone does NOT prove how a library is being used.

Do not describe a library's purpose unless the retrieved source code
provides evidence for that description.

For example:
- Do not say LangGraph is used for NLP simply because it appears
  in requirements.
- Say "LangGraph is present in the project dependencies" unless
  the source code demonstrates its specific usage.

When describing a file's purpose, inspect its retrieved content.

If its content was not retrieved, say:
"File exists, but its contents were not retrieved."

USER REQUEST:
{state["user_message"]}

VERIFIED GITHUB EVIDENCE:
{evidence_json}

Return:

## Verified Facts

Only facts explicitly supported by the evidence.

## Technology Stack

For each technology, provide:

Technology:
Evidence:
Confidence:

Rules:
- Only include a technology if it appears explicitly in retrieved
  file contents or repository metadata.
- Do not infer the purpose of a technology.
- Do not infer how a dependency is being used.
- If a technology appears only in requirements.txt, say:
  "Listed as a project dependency."
- If a technology appears in source code, quote or describe the
  relevant usage.
- Never describe LangGraph as an NLP library unless the retrieved
  source code explicitly demonstrates NLP usage.

## Project Structure

Do NOT generate this section.

The application will provide the verified project structure
separately from the GitHub tool.

Do not discuss directories or files in this section.

## Important Files

Only discuss paths that appear in the `file_contents` object.

Do not invent filenames.

Do not infer filenames from descriptions.

If a file is not in `file_contents`, do not describe its contents.

## Engineering Interpretation

You may make engineering interpretations, but they must be
supported by actual source-code evidence.

For every inference use:

Inference:
Evidence:
Reasoning:

IMPORTANT:

Do NOT infer the purpose of a library from its name alone.

Do NOT say:

"LangGraph is used for natural language processing."

unless the retrieved source code explicitly demonstrates
natural language processing functionality.

If the source code shows LangGraph being used to construct
nodes, edges, state, or workflows, describe that usage instead.

For example:

Inference:
LangGraph is used for agent workflow orchestration.

Evidence:
The retrieved eia_graph.py source defines graph nodes and
connects them into an execution graph.

Reasoning:
The observed graph structure indicates workflow orchestration.

## Potential Risks

Only identify risks supported by actual evidence.

## Recommended Next Steps

Provide practical engineering recommendations.

Never invent missing information.
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