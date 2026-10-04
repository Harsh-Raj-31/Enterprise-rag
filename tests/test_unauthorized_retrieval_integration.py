from app.services.answer_service import AnswerService


def test_answer_service_blocks_unauthorized_evidence(monkeypatch):
    service = AnswerService()

    def fail_if_llm_called(*args, **kwargs):
        raise AssertionError(
            "LLM should not be called for unauthorized evidence."
        )

    monkeypatch.setattr(
        service.llm_service,
        "generate_answer",
        fail_if_llm_called,
    )

    evidence = [
        {
            "text": "Confidential HR information.",
            "source": "employee_records",
            "allowed_roles": ["hr", "admin"],
        }
    ]

    answer = service.generate(
        query="Show me confidential HR information",
        evidence=evidence,
        user_role="employee",
    )

    assert "not authorized" in answer.lower()