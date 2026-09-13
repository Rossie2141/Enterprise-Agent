from langchain_core.messages import HumanMessage
from langgraph.types import Command
import time

from app.agents.graph import agent
from app.guardrails.input_guardrails import validate_input
from app.guardrails.output_guardrails import validate_output
from app.utils.logger import logger


def main():
    print("=== Enterprise AI Agent ===")
    print("Ask a question or type 'exit' / 'quit' to end the session.")

    while True:
        user_request = input("\nYou: ").strip()

        # ----------------------------------------------------
        # Exit
        # ----------------------------------------------------

        if user_request.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        # Ignore empty input
        if not user_request:
            continue

        logger.info("Request received: %s", user_request)

        # ----------------------------------------------------
        # Input guardrail
        # ----------------------------------------------------

        allowed, reason = validate_input(user_request)

        if not allowed:
            logger.warning("Input blocked: %s", reason)
            print(f"\n⚠️ Request blocked: {reason}")
            continue

        # ----------------------------------------------------
        # Agent configuration
        # ----------------------------------------------------

        config = {
            "configurable": {
                "thread_id": "cli-session"
            }
        }

        try:
            # ------------------------------------------------
            # Run agent
            # ------------------------------------------------

            start_time = time.perf_counter()
            logger.info("Starting agent execution")

            result = agent.invoke(
                {
                    "user_request": user_request,
                    "messages": [
                        HumanMessage(
                            content=user_request
                        )
                    ],
                },
                config=config,
            )

            logger.info("Agent execution completed")
            latency = time.perf_counter() - start_time

            logger.info(
                "Agent request completed in %.2f seconds",
                latency,
            )

            # ------------------------------------------------
            # Human-in-the-Loop
            # ------------------------------------------------

            while "__interrupt__" in result:

                interrupt_data = result[
                    "__interrupt__"
                ][0].value

                print("\n⚠️ APPROVAL REQUIRED")
                print(interrupt_data["message"])

                print(
                    f"Ticket ID: "
                    f"{interrupt_data['ticket_id']}"
                )

                if interrupt_data.get("new_status"):
                    print(
                        f"New status: "
                        f"{interrupt_data['new_status']}"
                    )

                if interrupt_data.get("new_priority"):
                    print(
                        f"New priority: "
                        f"{interrupt_data['new_priority']}"
                    )

                approval = input(
                    "\nApprove this action? (yes/no): "
                ).strip().lower()

                if approval in {"yes", "y"}:
                    logger.info("HITL action approved")
                    result = agent.invoke(
                        Command(resume=True),
                        config=config,
                    )
                else:
                    logger.info("HITL action rejected")
                    result = agent.invoke(
                        Command(resume=False),
                        config=config,
                    )

            # ------------------------------------------------
            # Display final response
            # ------------------------------------------------

            final_response = result["messages"][-1].content

            allowed, reason = validate_output(final_response)

            if allowed:
                logger.info("Output validation passed")
            else:
                logger.warning(
                    "Output validation blocked response: %s",
                    reason,
                )

            print("\nAgent:")

            if allowed:
                print(final_response)
            else:
                print(f"⚠️ Response blocked: {reason}")

        except Exception as e:
            logger.exception("Unexpected agent error")

            print(
                "\n❌ An unexpected error occurred. "
                "Please try again."
            )


if __name__ == "__main__":
    main()
