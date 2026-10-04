from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """
    Generate semantic embeddings for documents and queries.
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed_documents(
        self,
        texts: list[str]
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple documents.
        """
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True
        )

        return embeddings.tolist()

    def embed_query(
        self,
        query: str
    ) -> list[float]:
        """
        Generate an embedding for a user query.
        """
        embedding = self.model.encode(
            query,
            normalize_embeddings=True
        )

        return embedding.tolist()