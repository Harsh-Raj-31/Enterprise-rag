from typing import TypedDict


class AgentResult(TypedDict, total=False):
    """
    Standard result returned by every knowledge-source agent.
    """

    source_type: str
    answer: str
    evidence: list[dict]
    sources: list[dict]