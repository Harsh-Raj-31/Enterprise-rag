from app.services.llm_service import LLMService


def main():

    service = LLMService()

    query = "How many annual leave days do employees receive?"

    context = [
        {
            "text": (
                "Full-time employees receive 24 days "
                "of paid annual leave per calendar year."
            )
        }
    ]

    answer = service.generate_answer(
        query=query,
        context=context
    )

    print("\n" + "=" * 70)
    print("LLM SERVICE TEST")
    print("=" * 70)

    print("\nQuestion:")
    print(query)

    print("\nGenerated Response:")
    print(answer)


if __name__ == "__main__":
    main()