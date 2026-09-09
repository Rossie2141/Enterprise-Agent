from typing import TypedDict, List, Dict, Any


class AgentState(TypedDict, total=False):

    user_request: str

    messages: List[Dict[str, Any]]

    plan: List[str]

    tool_results: List[Dict[str, Any]]

    final_answer: str