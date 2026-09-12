from typing import TypedDict, Annotated, Sequence

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    """
    Shared state that flows through the LangGraph agent.
    """

    user_request: str

    messages: Annotated[Sequence[BaseMessage], add_messages]

    final_answer: str