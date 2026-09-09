from langgraph.graph import StateGraph, START, END

from app.agents.state import AgentState
from app.models.llm import get_llm


llm = get_llm()


def process_request(state: AgentState) -> AgentState:

    response = llm.invoke(state["user_request"])

    return {
        **state,
        "messages": [
            {
                "role": "assistant",
                "content": response.content,
            }
        ],
        "final_answer": response.content,
    }


def build_graph():

    graph = StateGraph(AgentState)

    graph.add_node("process_request", process_request)

    graph.add_edge(START, "process_request")
    graph.add_edge("process_request", END)

    return graph.compile()


agent = build_graph()