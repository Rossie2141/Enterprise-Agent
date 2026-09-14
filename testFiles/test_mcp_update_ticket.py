import asyncio

from app.mcp.client import call_mcp_tool


async def main():
    result = await call_mcp_tool(
        "update_ticket_mcp",
        {
            "ticket_id": "TCK-1001",
            "priority": "medium",
        },
    )

    for content in result.content:
        if hasattr(content, "text"):
            print(content.text)


if __name__ == "__main__":
    asyncio.run(main())