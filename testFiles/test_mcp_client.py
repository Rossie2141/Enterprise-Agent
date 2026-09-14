import asyncio

from app.mcp.client import list_mcp_tools, call_mcp_tool


async def main():
    tools = await list_mcp_tools()

    print("Discovered MCP tools:")

    for tool in tools:
        print(f"- {tool.name}")

    result = await call_mcp_tool(
        "search_tickets_mcp",
        {
            "status": "open",
            "priority": "high",
        },
    )

    print("\nMCP tool result:")

    for content in result.content:
        if hasattr(content, "text"):
            print(content.text)


if __name__ == "__main__":
    asyncio.run(main())