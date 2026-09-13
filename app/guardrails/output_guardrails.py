import re


# Patterns that should never appear in the final
# user-facing response.
BLOCKED_OUTPUT_PATTERNS = [
    r"system prompt",
    r"developer instructions",
    r"developer message",
    r"internal instructions",
    r"api[_ -]?key\s*=",
    r"traceback \(most recent call last\)",
]


def validate_output(response: str) -> tuple[bool, str]:
    """
    Validate the final response before showing it to the user.

    Returns:
        (True, "") when the response is safe.
        (False, reason) when the response should be blocked.
    """

    if not response or not response.strip():
        return False, "The agent returned an empty response."

    for pattern in BLOCKED_OUTPUT_PATTERNS:
        if re.search(pattern, response, re.IGNORECASE):
            return (
                False,
                "The response contained restricted internal information.",
            )

    return True, ""