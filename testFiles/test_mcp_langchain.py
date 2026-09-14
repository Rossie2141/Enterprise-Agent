from app.mcp.langchain_tools import mcp_search_tickets


result = mcp_search_tickets.invoke(
    {
        "status": "open",
        "priority": "high",
    }
)

print("LangChain MCP tool result:")
print(result)