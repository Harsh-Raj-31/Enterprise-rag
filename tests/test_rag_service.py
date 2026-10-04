from app.ingestion.pdf_loader import PDFLoader
from app.ingestion.chunker import TextChunker
from app.services.rag_service import RAGService


PDF_PATH = "data/raw/employee_policy.pdf"


def main():

    # 1. Load PDF
    loader = PDFLoader()

    documents = loader.load(
        PDF_PATH
    )

    # 2. Create chunks
    chunker = TextChunker(
        chunk_size=120,
        chunk_overlap=20
    )

    chunks = chunker.chunk_documents(
        documents
    )

    print(
        f"Chunks loaded: {len(chunks)}"
    )

    # 3. Create RAG service
    rag_service = RAGService(
        chunks
    )

    # 4. Ask question
    query = (
        "How many annual leave days "
        "do employees receive?"
    )

    result = rag_service.answer(
        query=query,
        top_k=3
    )

    print("\n" + "=" * 70)
    print("END-TO-END RAG TEST")
    print("=" * 70)

    print("\nQuestion:")
    print(result["query"])

    print("\nAnswer:")
    print(result["answer"])

    print("\nSources:")

    for index, source in enumerate(
        result["sources"],
        start=1
    ):
        print(
            f"\nSource {index}"
        )

        print(
            f"Source: "
            f"{source['source']}"
        )

        print(
            f"Page: "
            f"{source['page']}"
        )

        print(
            f"Chunk ID: "
            f"{source['chunk_id']}"
        )

        print(
            f"Rerank Score: "
            f"{source['rerank_score']:.4f}"
        )


if __name__ == "__main__":
    main()