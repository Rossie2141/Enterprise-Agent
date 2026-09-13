from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage
from app.utils.logger import logger

from app.agents.state import AgentState
from app.agents.router import route_request
from app.models.llm import get_llm
from langgraph.checkpoint.memory import InMemorySaver

from app.tools.ticket_tools import (
    search_tickets,
    get_ticket,
    update_ticket,
)

from app.tools.knowledge_tools import search_knowledge


llm = get_llm()


# All available tools
all_tools = [
    search_tickets,
    get_ticket,
    update_ticket,
    search_knowledge,
]


# Tool groups
ticket_tools = [
    search_tickets,
    get_ticket,
    update_ticket,
]

knowledge_tools = [
    search_knowledge,
]

mixed_tools = [
    search_tickets,
    get_ticket,
    update_ticket,
    search_knowledge,
]


def create_tool_node(tools):
    """Create a ToolNode for a specific tool group."""
    return ToolNode(tools)


ticket_tool_node = create_tool_node(ticket_tools)
knowledge_tool_node = create_tool_node(knowledge_tools)
mixed_tool_node = create_tool_node(mixed_tools)


def classify_request(state: AgentState) -> AgentState:
    """
    Classify the user's request before execution.
    """

    route = route_request(state["user_request"])

    logger.info("Router selected route: %s", route)

    return {
        **state,
        "route": route,
    }


def get_system_message(route: str) -> SystemMessage:
    """
    Create system instructions based on the selected route.
    """

    instructions = {
        "ticket": (
            "This is a ticket-related request.\n"
            "Use only the ticket tools available to you.\n"
            "Never invent ticket information.\n"
            "For ticket updates, always use update_ticket."
        ),

        "knowledge": (
            "This is an internal knowledge request.\n"
            "Use search_knowledge to retrieve relevant company "
            "policies, procedures, or documentation.\n"
            "Base your answer on the retrieved knowledge.\n"
            "Do not invent company policies."
        ),

        "mixed": (
            "This request requires both ticket information and "
            "internal company knowledge.\n"
            "Use the appropriate tools to retrieve both sources "
            "before answering.\n"
            "Clearly separate ticket information from policy or "
            "knowledge information when useful."
        ),

        "general": (
            "This is a general request.\n"
            "Answer normally, but do not invent company-specific "
            "information."
        ),
    }

    return SystemMessage(
        content=(
            "You are an enterprise support operations agent.\n\n"
            "General rules:\n"
            "1. Never invent information.\n"
            "2. Use the available tools when reliable information "
            "is required.\n"
            "3. Keep answers concise and operationally useful.\n"
            "4. Never claim a ticket was updated unless the "
            "update_ticket tool successfully performed the update.\n\n"
            f"Current route: {route}\n\n"
            f"Route instructions:\n{instructions[route]}"
        )
    )


def run_agent(
    state: AgentState,
    tools,
) -> AgentState:
    """
    Run the LLM with the tools allowed for the current route.
    """

    route = state.get("route", "general")

    llm_with_tools = llm.bind_tools(tools)

    system_message = get_system_message(route)

    messages = [
        system_message,
        *state["messages"],
    ]

    response = llm_with_tools.invoke(messages)
    if getattr(response, "tool_calls", None):
        for tool_call in response.tool_calls:
            logger.info(
                "Tool requested: %s",
                tool_call.get("name", "unknown"),
            )

    return {
        **state,
        "messages": state["messages"] + [response],
    }


def ticket_agent(state: AgentState) -> AgentState:
    """Execute the ticket route."""

    return run_agent(state, ticket_tools)


def knowledge_agent(state: AgentState) -> AgentState:
    """Execute the knowledge route."""

    return run_agent(state, knowledge_tools)


def mixed_agent(state: AgentState) -> AgentState:
    """Execute the mixed route."""

    return run_agent(state, mixed_tools)


def general_agent(state: AgentState) -> AgentState:
    """Execute the general route."""

    return run_agent(state, [])


def route_execution(state: AgentState):
    """
    Choose the execution path based on the router result.
    """

    route = state.get("route", "general")

    if route == "ticket":
        return "ticket_agent"

    if route == "knowledge":
        return "knowledge_agent"

    if route == "mixed":
        return "mixed_agent"

    return "general_agent"


def should_use_tools(state: AgentState):
    """
    Decide whether the current agent requested a tool.
    """

    last_message = state["messages"][-1]

    if getattr(last_message, "tool_calls", None):
        return "tools"

    return END


def select_tool_node(state: AgentState):
    """
    Execute a tool only when the LLM requested one.
    Otherwise, end the graph.
    """

    last_message = state["messages"][-1]

    # No tool call → finish
    if not getattr(last_message, "tool_calls", None):
        return END

    route = state.get("route", "general")

    if route == "ticket":
        return "ticket_tools"

    if route == "knowledge":
        return "knowledge_tools"

    if route == "mixed":
        return "mixed_tools"

    return END


def build_graph():
    """
    Build the LangGraph agent.
    """

    graph = StateGraph(AgentState)

    # Nodes
    graph.add_node(
        "classify_request",
        classify_request,
    )

    graph.add_node(
        "ticket_agent",
        ticket_agent,
    )

    graph.add_node(
        "knowledge_agent",
        knowledge_agent,
    )

    graph.add_node(
        "mixed_agent",
        mixed_agent,
    )

    graph.add_node(
        "general_agent",
        general_agent,
    )

    graph.add_node(
        "ticket_tools",
        ticket_tool_node,
    )

    graph.add_node(
        "knowledge_tools",
        knowledge_tool_node,
    )

    graph.add_node(
        "mixed_tools",
        mixed_tool_node,
    )

    # START → Router
    graph.add_edge(
        START,
        "classify_request",
    )

    # Router → appropriate agent
    graph.add_conditional_edges(
        "classify_request",
        route_execution,
        {
            "ticket_agent": "ticket_agent",
            "knowledge_agent": "knowledge_agent",
            "mixed_agent": "mixed_agent",
            "general_agent": "general_agent",
        },
    )

    # Agent → tools or END
    graph.add_conditional_edges(
        "ticket_agent",
        select_tool_node,
        {
            "ticket_tools": "ticket_tools",
            END: END,
        },
    )

    graph.add_conditional_edges(
        "knowledge_agent",
        select_tool_node,
        {
            "knowledge_tools": "knowledge_tools",
            END: END,
        },
    )

    graph.add_conditional_edges(
        "mixed_agent",
        select_tool_node,
        {
            "mixed_tools": "mixed_tools",
            END: END,
        },
    )

    # General agent has no tools
    graph.add_edge(
        "general_agent",
        END,
    )

    # Tools → their respective agent
    graph.add_edge(
        "ticket_tools",
        "ticket_agent",
    )

    graph.add_edge(
        "knowledge_tools",
        "knowledge_agent",
    )

    graph.add_edge(
        "mixed_tools",
        "mixed_agent",
    )

    # Memory
    checkpointer = InMemorySaver()

    return graph.compile(
        checkpointer=checkpointer
    )


agent = build_graph()