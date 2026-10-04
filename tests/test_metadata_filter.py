from app.retrieval.retriever import Retriever


def main():

    retriever = Retriever()

    query = "What are the working hours?"

    print("\n" + "=" * 70)
    print("METADATA FILTER TEST")
    print("=" * 70)

    print(f"\nQuery: {query}")

    results = retriever.retrieve(
        query=query,
        top_k=3,
        where={
            "source": "employee_policy.pdf"
        }
    )

    for index, result in enumerate(
        results,
        start=1
    ):
        metadata = result["metadata"]

        print(f"\nResult {index}")
        print(f"Source: {metadata['source']}")
        print(f"Page: {metadata['page']}")
        print(f"Chunk: {metadata['chunk_id']}")
        print(f"Distance: {result['distance']:.4f}")

        print("\nText:")
        print(result["text"][:500])


if __name__ == "__main__":
    main()