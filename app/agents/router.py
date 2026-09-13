from typing import Literal

from langchain_core.messages import HumanMessage
from app.models.llm import get_llm


Route = Literal["ticket", "knowledge", "mixed", "general"]


llm = get_llm()


ROUTER_PROMPT = """
You are a routing classifier for an enterprise support AI agent.

Classify the user's request into exactly ONE of these categories:

- ticket: The request is about support tickets, ticket status,
  ticket priority, ticket details, or updating a ticket.

- knowledge: The request is asking about company policies,
  procedures, troubleshooting instructions, or internal documentation.

- mixed: The request requires BOTH ticket information and
  internal company knowledge.

- general: The request does not require ticket data or internal
  company knowledge.

Return ONLY the category name:
ticket
knowledge
mixed
general
"""


def route_request(user_request: str) -> Route:
    """Classify a user request into an agent route."""

    response = llm.invoke(
        [
            HumanMessage(
                content=(
                    ROUTER_PROMPT
                    + "\n\nUser request:\n"
                    + user_request
                )
            )
        ]
    )

    route = response.content.strip().lower()

    if route not in {"ticket", "knowledge", "mixed", "general"}:
        return "general"

    return route