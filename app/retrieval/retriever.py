from app.retrieval.embeddings import EmbeddingService
from app.retrieval.vector_store import VectorStore


class Retriever:
    """
    Retrieval service that converts a user query into
    relevant document chunks.

    Supports optional role-based filtering so that
    unauthorized documents are excluded before retrieval
    results are returned.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        vector_store: VectorStore | None = None
    ):
        self.embedding_service = (
            embedding_service
            or EmbeddingService()
        )

        self.vector_store = (
            vector_store
            or VectorStore()
        )

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        where: dict | None = None,
        allowed_roles: list[str] | None = None
    ) -> list[dict]:
        """
        Retrieve the most relevant document chunks
        for a user query.

        If allowed_roles is provided, only documents
        whose metadata contains one of those roles
        will be retrieved.
        """

        if not query.strip():
            raise ValueError(
                "Query cannot be empty."
            )

        # Build role-based metadata filter
        if allowed_roles:
            normalized_roles = sorted({
                role.strip().lower()
                for role in allowed_roles
                if role.strip()
            })

            if not normalized_roles:
                raise ValueError(
                    "allowed_roles must contain at least one valid role."
                )

            role_filters = [
                {f"access_{role}": True}
                for role in normalized_roles
            ]

            if len(role_filters) == 1:
                role_filter = role_filters[0]
            else:
                role_filter = {
                    "$or": role_filters
                }
                
            if where:
                where = {
                    "$and": [
                        where,
                        role_filter
                    ]
                }
            else:
                where = role_filter

        # 1. Convert query into an embedding
        query_embedding = (
            self.embedding_service.embed_query(query)
        )

        # 2. Search vector database
        results = self.vector_store.search(
            query_embedding,
            top_k=top_k,
            where=where
        )

        # 3. Convert ChromaDB response into a clean format
        retrieved_documents = []

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for index, document in enumerate(documents):
            retrieved_documents.append(
                {
                    "text": document,
                    "metadata": metadatas[index],
                    "distance": distances[index]
                }
            )

        return retrieved_documents