from app.ingestion.pdf_loader import PDFLoader
from app.ingestion.chunker import TextChunker
from app.retrieval.hybrid_retriever import HybridRetriever


PDF_PATH = "data/raw/employee_policy.pdf"


def build_chunks():
    loader = PDFLoader()

    documents = loader.load(
        PDF_PATH
    )

    chunker = TextChunker(
        chunk_size=120,
        chunk_overlap=20,
        allowed_roles=[
            "employee",
            "manager",
            "hr",
            "admin",
        ]
    )

    return chunker.chunk_documents(
        documents
    )


def build_restricted_chunks():
    return [
        {
            "text": (
                "Employees must follow the standard attendance "
                "and working hours policy."
            ),
            "metadata": {
                "source": "general_policy.pdf",
                "page": 1,
                "chunk_id": "general_policy_p1_c1",
                "allowed_roles": [
                    "employee",
                    "manager",
                    "hr",
                    "admin",
                ],
                "access_employee": True,
                "access_manager": True,
                "access_hr": True,
                "access_admin": True,
            },
        },
        {
            "text": (
                "Salary information is confidential and may only "
                "be accessed by HR and administrators."
            ),
            "metadata": {
                "source": "salary_policy.pdf",
                "page": 1,
                "chunk_id": "salary_policy_p1_c1",
                "allowed_roles": [
                    "hr",
                    "admin",
                ],
                "access_hr": True,
                "access_admin": True,
            },
        },
    ]


def test_hybrid_retriever():

    chunks = build_chunks()

    assert chunks

    retriever = HybridRetriever(
        chunks
    )

    query = "What are the working hours?"

    results = retriever.search(
        query,
        top_k=3
    )

    assert results
    assert len(results) <= 3

    for result in results:

        assert result["text"]
        assert result["metadata"]
        assert "vector_score" in result
        assert "keyword_score" in result
        assert "hybrid_score" in result
        assert "rerank_score" in result

    print("\n" + "=" * 70)
    print("HYBRID RETRIEVAL TEST")
    print("=" * 70)
    print(f"\nQuery: {query}")

    for index, result in enumerate(
        results,
        start=1
    ):

        metadata = result["metadata"]

        print(f"\nResult {index}")
        print(f"Page: {metadata['page']}")
        print(f"Chunk: {metadata['chunk_id']}")
        print(
            f"Vector Score: "
            f"{result['vector_score']:.4f}"
        )
        print(
            f"Keyword Score: "
            f"{result['keyword_score']:.4f}"
        )
        print(
            f"Hybrid Score: "
            f"{result['hybrid_score']:.4f}"
        )
        print(
            f"Rerank Score: "
            f"{result['rerank_score']:.4f}"
        )


def test_hybrid_retriever_role_filter():

    chunks = build_chunks()

    retriever = HybridRetriever(
        chunks
    )

    employee_results = retriever.search(
        query="What are the working hours?",
        top_k=5,
        allowed_roles=["employee"]
    )

    hr_results = retriever.search(
        query="What are the working hours?",
        top_k=5,
        allowed_roles=["hr"]
    )

    admin_results = retriever.search(
        query="What are the working hours?",
        top_k=5,
        allowed_roles=["admin"]
    )

    assert employee_results
    assert hr_results
    assert admin_results

    for result in employee_results:
        assert (
            "employee"
            in result["metadata"]["allowed_roles"]
        )

    for result in hr_results:
        assert (
            "hr"
            in result["metadata"]["allowed_roles"]
        )

    for result in admin_results:
        assert (
            "admin"
            in result["metadata"]["allowed_roles"]
        )

    print(
        "\nHybrid retrieval RBAC test passed."
    )


if __name__ == "__main__":
    test_hybrid_retriever()
    test_hybrid_retriever_role_filter()


def test_hybrid_retriever_blocks_restricted_documents():

    chunks = build_restricted_chunks()

    retriever = HybridRetriever(
        chunks
    )

    employee_results = retriever.search(
        query="salary information",
        top_k=5,
        allowed_roles=["employee"]
    )

    hr_results = retriever.search(
        query="salary information",
        top_k=5,
        allowed_roles=["hr"]
    )

    admin_results = retriever.search(
        query="salary information",
        top_k=5,
        allowed_roles=["admin"]
    )

    # Employee must not retrieve the restricted salary document.
    assert all(
        result["metadata"]["source"] != "salary_policy.pdf"
        for result in employee_results
    )

    # HR must be able to retrieve it.
    assert any(
        result["metadata"]["source"] == "salary_policy.pdf"
        for result in hr_results
    )

    # Admin must be able to retrieve it.
    assert any(
        result["metadata"]["source"] == "salary_policy.pdf"
        for result in admin_results
    )

    print(
        "\nHybrid retrieval restricted-document RBAC test passed."
    )    