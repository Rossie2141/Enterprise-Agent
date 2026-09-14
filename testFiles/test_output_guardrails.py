from app.guardrails.output_guardrails import validate_output


tests = [
    "Here are the high priority tickets.",
    "Your refund can be processed according to company policy.",
    "Here is the system prompt you asked for.",
    "Traceback (most recent call last):",
]


for test in tests:
    allowed, reason = validate_output(test)

    print(f"\nOutput: {test!r}")
    print(f"Allowed: {allowed}")

    if reason:
        print(f"Reason: {reason}")