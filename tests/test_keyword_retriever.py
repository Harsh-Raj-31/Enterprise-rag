from app.ingestion.pdf_loader import PDFLoader
from app.ingestion.chunker import TextChunker
from app.retrieval.keyword_retriever import KeywordRetriever


PDF_PATH = "data/raw/employee_policy.pdf"


def build_chunks():
    loader = PDFLoader()
    documents = loader.load(PDF_PATH)

    chunker = TextChunker(
        chunk_size=120,
        chunk_overlap=20,
        allowed_roles=[
            "employee",
            "manager",
            "hr",
            "admin",
        ],
    )

    return chunker.chunk_documents(documents)


def test_keyword_retriever():

    chunks = build_chunks()

    assert chunks

    retriever = KeywordRetriever(chunks)

    queries = [
        "What are the working hours?",
        "How many annual leave days do employees receive?",
        "Can employees work from home?",
    ]

    for query in queries:

        results = retriever.search(
            query,
            top_k=3,
        )

        assert results
        assert len(results) <= 3

        for result in results:
            assert result["text"]
            assert result["metadata"]
            assert "score" in result

        print("\n" + "=" * 70)
        print(f"QUERY: {query}")
        print("=" * 70)

        for index, result in enumerate(
            results,
            start=1,
        ):
            metadata = result["metadata"]

            print(f"\nResult {index}")
            print(f"Score: {result['score']:.4f}")
            print(f"Page: {metadata['page']}")
            print(f"Chunk: {metadata['chunk_id']}")
            print(f"Roles: {metadata['allowed_roles']}")
            print("\nText:")
            print(result["text"][:500])


def test_keyword_retrieval_role_filter():

    chunks = build_chunks()
    retriever = KeywordRetriever(chunks)

    employee_results = retriever.search(
        "What are the working hours?",
        top_k=5,
        allowed_roles=["employee"],
    )

    hr_results = retriever.search(
        "What are the working hours?",
        top_k=5,
        allowed_roles=["hr"],
    )

    assert employee_results
    assert hr_results

    for result in employee_results:
        assert "employee" in result["metadata"]["allowed_roles"]

    for result in hr_results:
        assert "hr" in result["metadata"]["allowed_roles"]

    print("\nKeyword retrieval RBAC test passed.")


if __name__ == "__main__":
    test_keyword_retriever()
    test_keyword_retrieval_role_filter()