from app.models.llm import get_llm
from app.tools.ticket_tools import search_tickets


def main():
    llm = get_llm()

    llm_with_tools = llm.bind_tools([
        search_tickets
    ])

    response = llm_with_tools.invoke(
        "Find all unresolved high-priority tickets."
    )

    print("\nResponse:")
    print(response)

    print("\nTool calls:")
    print(response.tool_calls)


if __name__ == "__main__":
    main()