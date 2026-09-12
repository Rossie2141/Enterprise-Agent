from langchain_core.messages import HumanMessage

from app.models.llm import get_llm
from app.tools.ticket_tools import search_tickets


llm = get_llm()
llm_with_tools = llm.bind_tools([search_tickets])

response = llm_with_tools.invoke(
    [
        HumanMessage(
            content="Find all unresolved high-priority tickets."
        )
    ]
)

print("CONTENT:")
print(response.content)

print("\nTOOL CALLS:")
print(response.tool_calls)