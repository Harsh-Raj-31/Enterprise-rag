from app.agents.state import AgentState
from app.agents.result import AgentResult
from app.services.answer_service import AnswerService
from app.retrieval.retriever import Retriever


class SpreadsheetAgent:
    """
    Agent responsible for retrieving information
    from ingested CSV/XLSX spreadsheet data.
    """

    def __init__(self):
        self.retriever = Retriever()
        self.answer_service = AnswerService()

    def run(self, state: AgentState) -> AgentState:

        query = state["query"]
        user_role = state.get("user_role")

        # Retrieve spreadsheet data with RBAC filtering.
        retrieved_documents = self.retriever.retrieve(
            query=query,
            top_k=5,
            allowed_roles=[user_role] if user_role else None,
        )

        # Keep only spreadsheet documents.
        spreadsheet_documents = [
            document
            for document in retrieved_documents
            if document["metadata"].get("document_type")
            == "spreadsheet"
        ]

        evidence = []

        for item in spreadsheet_documents:

            metadata = item["metadata"]

            evidence.append({
                "text": item["text"],
                "source": metadata["source"],
                "row": metadata.get("row"),
                "sheet": metadata.get("sheet"),
                "chunk_id": metadata["chunk_id"],
                "distance": item["distance"],
            })

        if not evidence:
            answer = (
                "I could not find any authorized spreadsheet "
                "information relevant to your query."
            )
        else:
            answer = self.answer_service.generate(
                query=query,
                evidence=evidence,
                user_role=user_role,
            )

        agent_result: AgentResult = {
            "source_type": "spreadsheet",
            "answer": answer,
            "evidence": evidence,
            "sources": [
                {
                    "source": item["source"],
                    "row": item.get("row"),
                    "sheet": item.get("sheet"),
                    "chunk_id": item["chunk_id"],
                    "distance": item["distance"],
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