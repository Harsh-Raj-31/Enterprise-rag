from app.ingestion.pdf_loader import PDFLoader
from app.ingestion.chunker import TextChunker
from app.retrieval.embeddings import EmbeddingService
from app.retrieval.vector_store import VectorStore


class PDFIngestionService:
    def __init__(self):
        self.loader = PDFLoader()
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()

    def ingest(
        self,
        file_path: str,
        allowed_roles=None,
        source_name: str | None = None,
    ):
        documents = self.loader.load(file_path)

        if not documents:
            raise ValueError(
                "The PDF contains no extractable text."
            )

        if source_name:
            for document in documents:
                document["metadata"]["source"] = source_name

        chunker = TextChunker(
            allowed_roles=allowed_roles
        )

        chunks = chunker.chunk_documents(documents)

        if not chunks:
            raise ValueError(
                "No chunks were generated from the PDF."
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
            "document_type": "pdf",
            "chunks_ingested": len(chunks),
            "allowed_roles": allowed_roles,
        }