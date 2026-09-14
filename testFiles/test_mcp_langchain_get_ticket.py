from app.mcp.langchain_tools import mcp_get_ticket


result = mcp_get_ticket.invoke(
    {"ticket_id": "TCK-1001"}
)

print(result)