from langchain_core.messages import HumanMessage
from langgraph.types import Command

from app.agents.graph import agent


def main():
    print("=== Enterprise AI Agent ===")
    print("Ask a question or type 'exit' / 'quit' to end the session.")

    while True:
        user_request = input("\nYou: ").strip()

        if user_request.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        if not user_request:
            continue

        config = {
            "configurable": {
                "thread_id": "cli-session"
            }
        }

        result = agent.invoke(
            {
                "user_request": user_request,
                "messages": [
                    HumanMessage(content=user_request)
                ],
            },
            config=config,
        )

        while "__interrupt__" in result:
            interrupt_data = result["__interrupt__"][0].value

            print("\n⚠️  APPROVAL REQUIRED")
            print(interrupt_data["message"])

            print(f"Ticket ID: {interrupt_data['ticket_id']}")

            if interrupt_data["new_status"]:
                print(f"New status: {interrupt_data['new_status']}")

            if interrupt_data["new_priority"]:
                print(f"New priority: {interrupt_data['new_priority']}")

            approval = input("\nApprove this action? (yes/no): ").strip().lower()

            if approval in {"yes", "y"}:
                result = agent.invoke(
                    Command(resume=True),
                    config=config,
                )
            else:
                result = agent.invoke(
                    Command(resume=False),
                    config=config,
                )

        print("\nAgent:")
        print(result["messages"][-1].content)


if __name__ == "__main__":
    main()