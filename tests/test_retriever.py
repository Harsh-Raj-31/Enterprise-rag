from app.retrieval.retriever import Retriever


def test_retriever():
    retriever = Retriever()

    queries = [
        "How many annual leave days do employees receive?",
        "What are the working hours?",
        "Can employees work from home?"
    ]

    for query in queries:

        print("\n" + "=" * 70)
        print(f"QUERY: {query}")
        print("=" * 70)

        results = retriever.retrieve(
            query,
            top_k=3
        )

        assert results, f"No results returned for query: {query}"

        for index, result in enumerate(
            results,
            start=1
        ):
            metadata = result["metadata"]

            assert result["text"]
            assert metadata["source"]
            assert metadata["page"] is not None

            print(f"\nResult {index}")
            print(f"Source: {metadata['source']}")
            print(f"Page: {metadata['page']}")
            print(f"Distance: {result['distance']:.4f}")

            print("\nText:")
            print(result["text"][:500])