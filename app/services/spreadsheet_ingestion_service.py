from app.ingestion.spreadsheet_loader import SpreadsheetLoader
from app.ingestion.chunker import TextChunker
from app.retrieval.embeddings import EmbeddingService
from app.retrieval.vector_store import VectorStore


class SpreadsheetIngestionService:
    """Ingest CSV and Excel files into the vector knowledge base."""

    def __init__(self):
        self.loader = SpreadsheetLoader()
        self.chunker = TextChunker()
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()

    def ingest(
        self,
        file_path: str,
        allowed_roles: list[str] | None = None,
        source_name: str | None = None,
    ) -> dict:
        documents = self.loader.load(file_path)


        if source_name:
            for document in documents:
                document["metadata"]["source"] = source_name

        if not documents:
            raise ValueError(
                "No records were found in the spreadsheet."
            )

        chunker = TextChunker(
            allowed_roles=allowed_roles
        )

        chunks = chunker.chunk_documents(documents)

        if not chunks:
            raise ValueError(
                "No content chunks were created from the spreadsheet."
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
            "source": source_name or file_path,
            "document_type": "spreadsheet",
            "chunks_ingested": len(chunks),
            "allowed_roles": allowed_roles,
        }
