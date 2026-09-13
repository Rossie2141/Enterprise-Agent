
import asyncio

from langchain_core.tools import tool
from langgraph.types import interrupt

from app.mcp.client import call_mcp_tool


@tool
def mcp_search_tickets(
    status: str = "",
    priority: str = "",
) -> str:
    """
    Search enterprise support tickets through MCP.

    Args:
        status: Optional ticket status filter.
        priority: Optional ticket priority filter.

    Returns:
        Matching tickets as JSON.
    """
    result = asyncio.run(
        call_mcp_tool(
            "search_tickets_mcp",
            {
                "status": status,
                "priority": priority,
            },
        )
    )

    output = []

    for content in result.content:
        if hasattr(content, "text"):
            output.append(content.text)

    return "\n".join(output)


@tool
def mcp_get_ticket(
    ticket_id: str,
) -> str:
    """
    Retrieve a specific enterprise support ticket through MCP.

    Args:
        ticket_id: The ticket ID to retrieve.

    Returns:
        Ticket information as JSON.
    """
    result = asyncio.run(
        call_mcp_tool(
            "get_ticket_mcp",
            {
                "ticket_id": ticket_id,
            },
        )
    )

    output = []

    for content in result.content:
        if hasattr(content, "text"):
            output.append(content.text)

    return "\n".join(output)


@tool
def mcp_update_ticket(
    ticket_id: str,
    status: str = "",
    priority: str = "",
) -> str:
    """
    Update an enterprise support ticket through MCP
    after explicit human approval.

    Human approval is handled by LangGraph before the
    MCP write operation is executed.

    Args:
        ticket_id: The ticket ID to update.
        status: Optional new ticket status.
        priority: Optional new ticket priority.

    Returns:
        Updated ticket information as JSON.
    """

    requested_ticket_id = ticket_id.strip()
    requested_status = status.strip().lower()
    requested_priority = priority.strip().lower()

    valid_statuses = {
        "open",
        "pending",
        "resolved",
    }

    valid_priorities = {
        "low",
        "medium",
        "high",
    }

    # --------------------------------------------------------
    # Validate input before asking for approval
    # --------------------------------------------------------

    if (
        requested_status
        and requested_status not in valid_statuses
    ):
        return (
            f"Invalid status '{status}'. "
            "Allowed values: open, pending, resolved."
        )

    if (
        requested_priority
        and requested_priority not in valid_priorities
    ):
        return (
            f"Invalid priority '{priority}'. "
            "Allowed values: low, medium, high."
        )

    if not requested_status and not requested_priority:
        return "No update fields were provided."

    # --------------------------------------------------------
    # Verify ticket exists through MCP
    # --------------------------------------------------------

    ticket_result = asyncio.run(
        call_mcp_tool(
            "get_ticket_mcp",
            {
                "ticket_id": requested_ticket_id,
            },
        )
    )

    ticket_output = []

    for content in ticket_result.content:
        if hasattr(content, "text"):
            ticket_output.append(content.text)

    ticket_data = "\n".join(ticket_output)

    if '"error"' in ticket_data:
        return ticket_data

    # --------------------------------------------------------
    # Human approval
    #
    # This interrupt runs inside LangGraph, not inside MCP.
    # --------------------------------------------------------

    approval = interrupt(
        {
            "action": "update_ticket",
            "ticket_id": requested_ticket_id,
            "new_status": (
                requested_status or None
            ),
            "new_priority": (
                requested_priority or None
            ),
            "message": (
                f"Approve updating ticket "
                f"{requested_ticket_id}?"
            ),
        }
    )

    # --------------------------------------------------------
    # Human rejected the operation
    # --------------------------------------------------------

    if not approval:
        return (
            f'{{"status": "cancelled", '
            f'"message": "Update to ticket '
            f'{requested_ticket_id} was cancelled."}}'
        )

    # --------------------------------------------------------
    # Human approved → MCP performs the database write
    # --------------------------------------------------------

    result = asyncio.run(
        call_mcp_tool(
            "update_ticket_mcp",
            {
                "ticket_id": requested_ticket_id,
                "status": requested_status,
                "priority": requested_priority,
            },
        )
    )

    output = []

    for content in result.content:
        if hasattr(content, "text"):
            output.append(content.text)

    return "\n".join(output)

