import logging


logger = logging.getLogger(__name__)


def handle_tool_error(
    tool_name: str,
    error: Exception,
) -> str:
    """
    Log a tool failure and return a safe message
    that can be passed back to the agent.
    """

    logger.error(
        "Tool '%s' failed: %s",
        tool_name,
        error,
        exc_info=True,
    )

    return (
        f"The {tool_name} tool could not complete the request. "
        "Please try again."
    )