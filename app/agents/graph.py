from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage

from app.agents.state import AgentState
from app.models.llm import get_llm
from langgraph.checkpoint.memory import InMemorySaver
from app.tools.ticket_tools import search_tickets, get_ticket, update_ticket


llm = get_llm()

tools = [search_tickets, get_ticket, update_ticket]

llm_with_tools = llm.bind_tools(tools)

tool_node = ToolNode(tools)


def call_model(state: AgentState) -> dict:
    """
    Ask the LLM what to do next.
    """

    response = llm_with_tools.invoke(state["messages"])

    result = {
        "messages": [response],
    }

    if not getattr(response, "tool_calls", None) and response.content:
        result["final_answer"] = response.content

    return result


def should_use_tools(state: AgentState):
    """
    Decide whether the LLM requested a tool.
    """

    last_message = state["messages"][-1]

    if getattr(last_message, "tool_calls", None):
        return "tools"

    return END


def build_graph():
    """
    Build the LangGraph agent.
    """

    graph = StateGraph(AgentState)

    graph.add_node("call_model", call_model)
    graph.add_node("tools", tool_node)

    graph.add_edge(START, "call_model")

    graph.add_conditional_edges(
        "call_model",
        should_use_tools,
    )

    graph.add_edge("tools", "call_model")

    checkpointer = InMemorySaver()

    return graph.compile(checkpointer=checkpointer)


agent = build_graph()