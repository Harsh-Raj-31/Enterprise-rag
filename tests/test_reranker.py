from app.ingestion.pdf_loader import PDFLoader
from app.ingestion.chunker import TextChunker
from app.retrieval.reranker import Reranker


PDF_PATH = "data/raw/employee_policy.pdf"


def main():

    # Load PDF
    loader = PDFLoader()
    documents = loader.load(PDF_PATH)

    # Create chunks
    chunker = TextChunker(
        chunk_size=120,
        chunk_overlap=20
    )

    chunks = chunker.chunk_documents(
        documents
    )

    # Create reranker
    reranker = Reranker()

    query = "What are the working hours?"

    # Use all chunks as candidates for this test
    candidates = [
        {
            "text": chunk["text"],
            "metadata": chunk["metadata"]
        }
        for chunk in chunks
    ]

    print("\n" + "=" * 70)
    print("RERANKER TEST")
    print("=" * 70)

    print(f"\nQuery: {query}")

    results = reranker.rerank(
        query=query,
        candidates=candidates,
        top_k=3
    )

    for index, result in enumerate(
        results,
        start=1
    ):

        metadata = result["metadata"]

        print(f"\nResult {index}")

        print(
            f"Page: {metadata['page']}"
        )

        print(
            f"Chunk: {metadata['chunk_id']}"
        )

        print(
            f"Rerank Score: "
            f"{result['rerank_score']:.4f}"
        )

        print("\nText:")
        print(
            result["text"][:500]
        )


if __name__ == "__main__":
    main()