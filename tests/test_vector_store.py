from app.ingestion.pdf_loader import PDFLoader
from app.ingestion.chunker import TextChunker
from app.retrieval.embeddings import EmbeddingService
from app.retrieval.vector_store import VectorStore


PDF_PATH = "data/raw/employee_policy.pdf"


def main():

    # -----------------------------------
    # 1. Load PDF
    # -----------------------------------

    loader = PDFLoader()

    documents = loader.load(PDF_PATH)

    print(f"Pages loaded: {len(documents)}")


    # -----------------------------------
    # 2. Create chunks
    # -----------------------------------

    chunker = TextChunker(
        chunk_size=120,
        chunk_overlap=20,
        allowed_roles=[
        "employee",
        "manager",
        "hr",
        "admin"
      ]
    )

    chunks = chunker.chunk_documents(
        documents
    )

    print(f"Chunks created: {len(chunks)}")


    # -----------------------------------
    # 3. Create embeddings
    # -----------------------------------

    embedding_service = EmbeddingService()

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    embeddings = embedding_service.embed_documents(
        texts
    )

    print(
        f"Embeddings created: {len(embeddings)}"
    )

    print(
        f"Embedding dimensions: {len(embeddings[0])}"
    )


    # -----------------------------------
    # 4. Store in ChromaDB
    # -----------------------------------

    vector_store = VectorStore()

    vector_store.add_documents(
        chunks,
        embeddings
    )

    print(
        f"Chunks in ChromaDB: "
        f"{vector_store.count()}"
    )


    # -----------------------------------
    # 5. Test semantic search
    # -----------------------------------

    query = (
        "How many annual leave days "
        "do employees receive?"
    )

    query_embedding = (
        embedding_service.embed_query(query)
    )

    results = vector_store.search(
        query_embedding,
        top_k=3
    )


    # -----------------------------------
    # 6. Display results
    # -----------------------------------

    print("\n" + "=" * 70)

    print(
        f"QUERY: {query}"
    )

    print("=" * 70)

    for index, document in enumerate(
        results["documents"][0],
        start=1
    ):

        metadata = results["metadatas"][0][
            index - 1
        ]

        print(
            f"\nResult {index}"
        )

        print(
            f"Source: {metadata['source']}"
        )

        print(
            f"Page: {metadata['page']}"
        )

        print(
            f"Chunk: {metadata['chunk_id']}"
        )

        print(
            f"\nText:\n{document}"
        )


if __name__ == "__main__":
    main()