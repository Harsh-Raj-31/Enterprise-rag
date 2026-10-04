from app.services.answer_service import AnswerService


def test_unsupported_answer_when_no_evidence():
    service = AnswerService()

    answer = service.generate(
        query="What is the company's policy on international relocation?",
        evidence=[],
    )

    assert answer == (
        "I could not find relevant information "
        "in the available knowledge sources."
    )


def test_unsupported_answer_when_evidence_is_irrelevant():
    service = AnswerService()

    evidence = [
        {
            "text": (
                "Full-time employees receive 24 days "
                "of paid annual leave per calendar year."
            ),
            "source": "employee_policy.pdf",
            "page": 1,
        }
    ]

    answer = service.generate(
        query="What is the company's international relocation policy?",
        evidence=evidence,
    )

    answer_lower = answer.lower()

    assert (
        "not available" in answer_lower
        or "not found" in answer_lower
        or "could not provide a reliable answer" in answer_lower
        or "could not find relevant information" in answer_lower
    )