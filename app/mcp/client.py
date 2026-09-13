from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


server_params = StdioServerParameters(
    command="python3",
    args=["-m", "app.mcp.server"],
)


@asynccontextmanager
async def get_mcp_session():
    """
    Create a connection to the Enterprise AI MCP server.
    """

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


async def list_mcp_tools():
    """
    Discover tools exposed by the MCP server.
    """

    async with get_mcp_session() as session:
        result = await session.list_tools()
        return result.tools


async def call_mcp_tool(
    tool_name: str,
    arguments: dict,
):
    """
    Call a tool exposed by the MCP server.
    """

    async with get_mcp_session() as session:
        return await session.call_tool(
            tool_name,
            arguments,
        )