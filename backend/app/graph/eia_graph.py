from langgraph.graph import END, START, StateGraph

from app.agents.eia_agent import run_eia
from app.graph.state import EIAState


def eia_node(state: EIAState) -> EIAState:
    response = run_eia(state["user_message"])

    return {
        **state,
        "response": response,
    }


builder = StateGraph(EIAState)

builder.add_node("eia", eia_node)

builder.add_edge(START, "eia")
builder.add_edge("eia", END)

eia_graph = builder.compile()