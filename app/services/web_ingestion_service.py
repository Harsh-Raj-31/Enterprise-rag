from app.ingestion.web_loader import WebLoader
from app.ingestion.chunker import TextChunker
from app.retrieval.embeddings import EmbeddingService
from app.retrieval.vector_store import VectorStore


class WebIngestionService:
    """
    Ingest website content into the enterprise vector knowledge base.
    """

    def __init__(self):
        self.loader = WebLoader()
        self.chunker = None
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()

    def ingest(
        self,
        url: str,
        allowed_roles: list[str] | None = None,
    ) -> dict:
        """
        Fetch, clean, chunk, embed and persist a website.
        """

        documents = self.loader.load(url)

        self.chunker = TextChunker(
            allowed_roles=allowed_roles,
        )

        chunks = self.chunker.chunk_documents(
            documents
        )

        if not chunks:
            raise ValueError(
                "No content chunks were created from the website."
            )

        texts = [
            chunk["text"]
            for chunk in chunks
        ]

        embeddings = self.embedding_service.embed_documents(
            texts
        )

        self.vector_store.add_documents(
            chunks=chunks,
            embeddings=embeddings,
        )

        return {
            "source": url,
            "document_type": "website",
            "chunks_ingested": len(chunks),
        }