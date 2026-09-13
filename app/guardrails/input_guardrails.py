import re


# Patterns for requests that should not be sent
# to the enterprise agent.
BLOCKED_PATTERNS = [
    r"\bignore (all|any|the) previous instructions\b",
    r"\bignore your instructions\b",
    r"\bdisregard (all|any|the) previous instructions\b",
    r"\breveal (your|the) system prompt\b",
    r"\bshow (me )?(your|the) system prompt\b",
    r"\bdeveloper instructions\b",
]


def validate_input(user_request: str) -> tuple[bool, str]:
    """
    Validate a user's request before it reaches the agent.

    Returns:
        (True, "") when the request is allowed.
        (False, reason) when the request should be blocked.
    """

    if not user_request or not user_request.strip():
        return False, "Request cannot be empty."

    request = user_request.strip()

    if len(request) > 4000:
        return (
            False,
            "Request is too long. Please keep it under 4000 characters.",
        )

    normalized_request = request.lower()

    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, normalized_request):
            return (
                False,
                "This request cannot be processed by the agent.",
            )

    return True, ""