from mcp.server.fastmcp import FastMCP

from app.tools.ticket_tools import search_tickets
import json 


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
        Matching support tickets.
    """

    result = search_tickets.invoke(
        {
            "status": status,
            "priority": priority,
        }
    )

    return json.dumps(result, default=str)


if __name__ == "__main__":
    mcp.run()