from typing import TypedDict


class AgentState(TypedDict, total=False):
    query: str
    route: str
    answer: str
    evidence: list[dict]
    sources: list[dict]
    url: str

    # Authenticated user's role used for RBAC
    user_role: str