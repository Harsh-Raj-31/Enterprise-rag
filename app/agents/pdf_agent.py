from app.agents.state import AgentState
from app.agents.result import AgentResult
from app.services.rag_service import RAGService
from app.services.answer_service import AnswerService


class PDFAgent:
    """
    Agent responsible for retrieving relevant
    information from PDF-based knowledge sources.
    """

    def __init__(self, chunks: list[dict]):
        self.rag_service = RAGService(chunks)
        self.answer_service = AnswerService()

    def run(self, state: AgentState) -> AgentState:

        query = state["query"]
        user_role = state.get("user_role")

        # Step 1: Retrieve and rerank evidence
        retrieved_chunks = self.rag_service.retrieve(
            query=query,
            top_k=3,
            allowed_roles=[user_role] if user_role else None,
        )

        # Step 2: Convert retrieved chunks
        # into standardized agent evidence
        evidence = []

        for item in retrieved_chunks:

            metadata = item["metadata"]

            evidence.append({
                "text": item["text"],
                "source": metadata["source"],
                "page": metadata["page"],
                "chunk_id": metadata["chunk_id"],
                "rerank_score": item["rerank_score"],
            })

        # Step 3: Generate the final answer
        # through the common answer-generation layer
        answer = self.answer_service.generate(
            query=query,
            evidence=evidence,
            user_role=user_role,
        )

        agent_result: AgentResult = {
            "source_type": "pdf",
            "answer": answer,
            "evidence": evidence,
            "sources": [
                {
                    "source": item["source"],
                    "page": item["page"],
                    "chunk_id": item["chunk_id"],
                    "rerank_score": item["rerank_score"],
                    "text": item["text"],
                }
                for item in evidence
            ],
        }

        return {
            **state,
            "answer": agent_result["answer"],
            "evidence": agent_result["evidence"],
            "sources": agent_result["sources"],
        }