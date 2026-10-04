from app.retrieval.hybrid_retriever import HybridRetriever
from app.services.llm_service import LLMService


class RAGService:
    """
    Service responsible for retrieval and
    grounded answer generation.
    """

    def __init__(self, chunks: list[dict]):
        self.retriever = HybridRetriever(chunks)
        self.llm_service = LLMService()


    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        allowed_roles: list[str] | None = None,
    ) -> list[dict]:

        if not query.strip():
            raise ValueError("Query cannot be empty.")

        return self.retriever.search(
            query=query,
            top_k=top_k,
            allowed_roles=allowed_roles,
        )

    def answer(
        self,
        query: str,
        top_k: int = 3,
    ) -> dict:

        retrieved_chunks = self.retrieve(
            query=query,
            top_k=top_k,
        )

        answer = self.llm_service.generate_answer(
            query=query,
            context=retrieved_chunks,
        )

        sources = []

        for chunk in retrieved_chunks:

            metadata = chunk["metadata"]

            sources.append({
                "source": metadata["source"],
                "page": metadata["page"],
                "chunk_id": metadata["chunk_id"],
                "rerank_score": chunk["rerank_score"],
                "text": chunk["text"],
            })

        return {
            "query": query,
            "answer": answer,
            "sources": sources,
        }