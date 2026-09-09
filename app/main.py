import sys
from pathlib import Path

# Ensure project root is in sys.path when running directly
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.agents.graph import agent


def main():
    user_request = input("You: ")

    result = agent.invoke(
        {
            "user_request": user_request
        }
    )

    print("\nAgent:")
    print(result["final_answer"])


if __name__ == "__main__":
    main()