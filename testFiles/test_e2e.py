import time
import re
import unicodedata
from dataclasses import dataclass

from groq import RateLimitError
from langchain_core.messages import HumanMessage, ToolMessage

from app.agents.graph import agent
from app.agents.router import route_request


# ============================================================
# Retry helper
# ============================================================

def invoke_with_retry(invoke_fn, max_retries=3):
    """
    Retry Groq requests when a temporary rate limit occurs.
    """

    for attempt in range(max_retries):
        try:
            return invoke_fn()

        except RateLimitError:
            if attempt == max_retries - 1:
                raise

            wait_time = 2 ** attempt

            print(
                f"[Rate limit] Waiting {wait_time}s before retry..."
            )

            time.sleep(wait_time)


# ============================================================
# Text normalization
# ============================================================

def normalize_text(text: str) -> str:
    """
    Normalize text for robust evaluation.

    Handles:
    - Unicode punctuation
    - Unicode hyphens/dashes
    - non-breaking spaces
    - repeated whitespace
    - markdown formatting
    """

    text = unicodedata.normalize("NFKC", text)
    text = text.lower()

    # Normalize common dash/hyphen variants
    dash_chars = "‐-‒–—―−"

    for char in dash_chars:
        text = text.replace(char, "-")

    # Normalize whitespace
    text = text.replace("\u00a0", " ")
    text = text.replace("\u202f", " ")

    # Remove markdown emphasis characters
    text = re.sub(r"[*_`]", "", text)

    # Collapse repeated whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# Test case definition
# ============================================================

@dataclass
class TestCase:
    name: str
    query: str
    expected_route: str
    expected_facts: list[list[str]]
    expected_tools: list[str]


# ============================================================
# Evaluation test cases
# ============================================================

TEST_CASES = [

    TestCase(
        "High priority tickets",
        "Find all unresolved high-priority tickets.",
        "ticket",
        [
            ["TCK-1001"],
            ["TCK-1003"],
            ["TCK-1007"],
        ],
        ["search_tickets"],
    ),

    TestCase(
        "Specific ticket lookup",
        "Show me the details for ticket TCK-1001.",
        "ticket",
        [
            ["TCK-1001"],
            ["CUST-001"],
            ["Payment failure"],
        ],
        ["get_ticket"],
    ),

    TestCase(
        "Refund policy",
        "What is the refund policy?",
        "knowledge",
        [
            ["30 days"],
            ["5-7 business days", "5 to 7 business days"],
        ],
        ["search_knowledge"],
    ),

    TestCase(
        "Password reset policy",
        "How do customers reset their password?",
        "knowledge",
        [
            [
                "verify ownership",
                "prove ownership",
                "owns the account",
                "ownership of the account",
            ],
            ["30 minutes"],
        ],
        ["search_knowledge"],
    ),

    TestCase(
        "API incident policy",
        "What should support do during a production API incident?",
        "knowledge",
        [
            [
                "high priority",
                "high-priority",
                "treated as high",
            ],
            ["engineering"],
            ["customer impact"],
        ],
        ["search_knowledge"],
    ),

    TestCase(
        "Mixed ticket and policy",
        "What is the refund policy and which high-priority tickets are currently open?",
        "mixed",
        [
            ["30 days"],
            ["5-7 business days", "5 to 7 business days"],
            ["TCK-1001"],
            ["TCK-1007"],
        ],
        [
            "search_knowledge",
            "search_tickets",
        ],
    ),

    TestCase(
        "General conversation",
        "Hello, how are you?",
        "general",
        [],
        [],
    ),

    TestCase(
        "Unknown company policy",
        "What is the employee vacation policy?",
        "knowledge",
        [
            [
                "unable to locate",
                "wasn't able to locate",
                "couldn't locate",
                "was not able to locate",
            ],
        ],
        ["search_knowledge"],
    ),

    TestCase(
        "Unknown ticket",
        "Show me the details for ticket TCK-9999.",
        "ticket",
        [
            ["TCK-9999"],
            [
                "unable to locate",
                "couldn't locate",
                "couldn't find",
                "not found",
            ],
        ],
        ["get_ticket"],
    ),

    TestCase(
        "Ticket status",
        "Which tickets are currently pending?",
        "ticket",
        [
            ["TCK-1003"],
            ["TCK-1008"],
        ],
        ["search_tickets"],
    ),
]


# ============================================================
# Run individual test
# ============================================================

def run_test(test_case, index):

    print("\n" + "=" * 60)
    print(f"TEST {index}: {test_case.name}")
    print("=" * 60)

    print(f"Query: {test_case.query}")
    print(f"Expected route: {test_case.expected_route}")

    # --------------------------------------------------------
    # 1. Test router
    # --------------------------------------------------------

    start_time = time.perf_counter()

    actual_route = invoke_with_retry(
        lambda: route_request(test_case.query)
    )

    route_time = time.perf_counter() - start_time

    route_passed = (
        actual_route == test_case.expected_route
    )

    print(f"Actual route:   {actual_route}")
    print(f"Router latency: {route_time:.2f}s")
    print(
        "Route result:",
        "PASS" if route_passed else "FAIL"
    )

    # --------------------------------------------------------
    # 2. Run complete LangGraph agent
    # --------------------------------------------------------

    start_time = time.perf_counter()

    result = invoke_with_retry(
        lambda: agent.invoke(
            {
                "user_request": test_case.query,
                "messages": [
                    HumanMessage(
                        content=test_case.query
                    )
                ],
            },
            config={
                "configurable": {
                    "thread_id": f"eval-{index}"
                }
            },
        )
    )

    agent_time = time.perf_counter() - start_time

    # --------------------------------------------------------
    # 3. Extract final answer
    # --------------------------------------------------------

    final_answer = result["messages"][-1].content

    normalized_answer = normalize_text(
        final_answer
    )

    # --------------------------------------------------------
    # 4. Evaluate answer facts
    # --------------------------------------------------------

    missing_facts = []

    for fact_options in test_case.expected_facts:

        fact_found = any(
            normalize_text(option) in normalized_answer
            for option in fact_options
        )

        if not fact_found:
            missing_facts.append(
                " / ".join(fact_options)
            )

    answer_passed = (
        len(missing_facts) == 0
    )

    print(
        "Answer result:",
        "PASS" if answer_passed else "FAIL"
    )

    if missing_facts:

        print("Missing facts:")

        for fact in missing_facts:
            print(f"  - {fact}")

    # --------------------------------------------------------
    # 5. Evaluate tool calls
    # --------------------------------------------------------

    actual_tools = []

    for message in result["messages"]:

        if isinstance(message, ToolMessage):

            if message.name:
                actual_tools.append(
                    message.name
                )

    # Remove duplicates while preserving order
    actual_tools = list(
        dict.fromkeys(actual_tools)
    )

    expected_tools = test_case.expected_tools

    # Strict comparison for now.
    # This checks both tool selection and order.
    tool_passed = (
        actual_tools == expected_tools
    )

    print(
        f"Expected tools: {expected_tools}"
    )

    print(
        f"Actual tools:   {actual_tools}"
    )

    print(
        "Tool result:",
        "PASS" if tool_passed else "FAIL"
    )

    # --------------------------------------------------------
    # 6. Display final answer
    # --------------------------------------------------------

    print(f"Agent latency:  {agent_time:.2f}s")

    print("\nFinal answer:")
    print(final_answer)

    # --------------------------------------------------------
    # Return evaluation result
    # --------------------------------------------------------

    return {
        "route_passed": route_passed,
        "answer_passed": answer_passed,
        "tool_passed": tool_passed,
        "route_time": route_time,
        "agent_time": agent_time,
        "answer": final_answer,
    }


# ============================================================
# Main evaluation
# ============================================================

def main():

    print("=" * 60)
    print("END-TO-END AGENT EVALUATION")
    print("=" * 60)

    results = []

    # --------------------------------------------------------
    # Run all tests
    # --------------------------------------------------------

    for index, test_case in enumerate(
        TEST_CASES,
        start=1
    ):

        result = run_test(
            test_case,
            index
        )

        results.append(result)

        # Small delay to reduce Groq rate-limit risk
        time.sleep(1)

    # --------------------------------------------------------
    # Calculate metrics
    # --------------------------------------------------------

    total_tests = len(results)

    route_passes = sum(
        result["route_passed"]
        for result in results
    )

    answer_passes = sum(
        result["answer_passed"]
        for result in results
    )

    tool_passes = sum(
        result["tool_passed"]
        for result in results
    )

    route_accuracy = (
        route_passes
        / total_tests
        * 100
    )

    answer_accuracy = (
        answer_passes
        / total_tests
        * 100
    )

    tool_accuracy = (
        tool_passes
        / total_tests
        * 100
    )

    average_latency = (
        sum(
            result["agent_time"]
            for result in results
        )
        / total_tests
    )

    # --------------------------------------------------------
    # Evaluation summary
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)

    print(f"Total tests:       {total_tests}")

    print(
        f"Route passes:      {route_passes}"
    )

    print(
        f"Route accuracy:    {route_accuracy:.1f}%"
    )

    print(
        f"Answer passes:     {answer_passes}"
    )

    print(
        f"Answer accuracy:   {answer_accuracy:.1f}%"
    )

    print(
        f"Tool passes:       {tool_passes}"
    )

    print(
        f"Tool accuracy:     {tool_accuracy:.1f}%"
    )

    print(
        f"Average latency:   {average_latency:.2f}s"
    )

    print("=" * 60)


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":
    main()