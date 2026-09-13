import json

from mcp.server.fastmcp import FastMCP

from app.tools.ticket_tools import (
    search_tickets,
    get_ticket,
    _update_ticket_db,
)


mcp = FastMCP("Enterprise AI Tools")


@mcp.tool()
def search_tickets_mcp(
    status: str = "",
    priority: str = "",
) -> str:
    """
    Search enterprise support tickets.

    Args:
        status: Optional ticket status filter.
        priority: Optional ticket priority filter.

    Returns:
        Matching support tickets as JSON.
    """
    result = search_tickets.invoke(
        {
            "status": status,
            "priority": priority,
        }
    )

    return json.dumps(
        result,
        default=str,
    )


@mcp.tool()
def get_ticket_mcp(
    ticket_id: str,
) -> str:
    """
    Retrieve a specific enterprise support ticket through MCP.

    Args:
        ticket_id: The ticket ID to retrieve.

    Returns:
        Ticket information as JSON.
    """
    result = get_ticket.invoke(
        {
            "ticket_id": ticket_id,
        }
    )

    return json.dumps(
        result,
        default=str,
    )


@mcp.tool()
def update_ticket_mcp(
    ticket_id: str,
    status: str = "",
    priority: str = "",
) -> str:
    """
    Update an enterprise support ticket through MCP.

    This tool performs the database mutation only.
    Human approval must be handled by the LangGraph agent
    before this tool is invoked.

    Args:
        ticket_id: The ticket ID to update.
        status: Optional new ticket status.
        priority: Optional new ticket priority.

    Returns:
        Updated ticket information as JSON.
    """
    result = _update_ticket_db(
        ticket_id=ticket_id,
        status=status,
        priority=priority,
    )

    return json.dumps(
        result,
        default=str,
    )


if __name__ == "__main__":
    mcp.run()

