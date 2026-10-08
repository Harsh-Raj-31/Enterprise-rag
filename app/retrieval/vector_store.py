import chromadb


class VectorStore:
    """
    ChromaDB vector store for enterprise document chunks.
    """

    def __init__(
        self,
        persist_directory: str = "chroma_db",
        collection_name: str = "enterprise_knowledge"
    ):
        self.client = chromadb.PersistentClient(
            path=persist_directory
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={
                "description": "Enterprise RAG knowledge base"
            }
        )

    def add_documents(
        self,
        chunks: list[dict],
        embeddings: list[list[float]]
    ):
        """
        Store chunks, embeddings and metadata in ChromaDB.
        """

        ids = [
            chunk["metadata"]["chunk_id"]
            for chunk in chunks
        ]

        documents = [
            chunk["text"]
            for chunk in chunks
        ]

        metadatas = [
            chunk["metadata"]
            for chunk in chunks
        ]

        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 3,
        where: dict | None = None
    ):
        """
        Search for semantically similar chunks.

        Optional metadata filtering can be applied
        using the `where` parameter.
        """

        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where
        )

    def count(self) -> int:
        """
        Return number of stored chunks.
        """

        return self.collection.count()

    def delete_documents(
        self,
        ids: list[str],
    ):
        """
        Delete specific document chunks by ID.
        """

        if not ids:
            return

        self.collection.delete(
            ids=ids
        )

    def delete_by_source(
        self,
        source: str,
    ):
        """
        Delete all document chunks belonging to a source.
        """

        if not source or not source.strip():
            raise ValueError(
                "Source cannot be empty."
            )

        results = self.collection.get(
            where={
                "source": source.strip()
            },
            include=[],
        )

        ids = results.get("ids", [])

        if ids:
            self.collection.delete(
                ids=ids
            )

        return {
            "source": source.strip(),
            "deleted_chunks": len(ids),
        }
