from app.services.llm_service import LLMService


def main():

    service = LLMService()

    context = [
        {
            "text": (
                "Full-time employees receive "
                "24 days of paid annual leave "
                "per calendar year."
            ),
            "metadata": {
                "source": "employee_policy.pdf",
                "page": 2,
            },
        }
    ]

    answer = service.generate_answer(
        query=(
            "How many annual leave days "
            "do employees receive?"
        ),
        context=context,
    )

    print("\n==============================")
    print("LLM RESPONSE")
    print("==============================")
    print(answer)
    print("==============================")


if __name__ == "__main__":
    main()