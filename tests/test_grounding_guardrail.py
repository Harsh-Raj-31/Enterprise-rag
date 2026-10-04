from app.guardrails.grounding import GroundingGuardrail


def test_grounded_answer_passes():

    guardrail = GroundingGuardrail()

    evidence = [
        {
            "text": (
                "Full-time employees receive "
                "24 days of paid annual leave "
                "per calendar year."
            )
        }
    ]

    answer = (
        "Full-time employees receive "
        "24 days of paid annual leave."
    )

    assert guardrail.validate(
        answer=answer,
        evidence=evidence,
    ) is True


def test_unsupported_answer_fails():

    guardrail = GroundingGuardrail()

    evidence = [
        {
            "text": (
                "Full-time employees receive "
                "24 days of paid annual leave "
                "per calendar year."
            )
        }
    ]

    answer = (
        "Full-time employees receive "
        "30 days of paid annual leave."
    )

    assert guardrail.validate(
        answer=answer,
        evidence=evidence,
    ) is False


def test_empty_evidence_fails():

    guardrail = GroundingGuardrail()

    answer = "Employees receive 24 days of annual leave."

    assert guardrail.validate(
        answer=answer,
        evidence=[],
    ) is False


def test_empty_answer_fails():

    guardrail = GroundingGuardrail()

    evidence = [
        {
            "text": "Employees receive 24 days of annual leave."
        }
    ]

    assert guardrail.validate(
        answer="",
        evidence=evidence,
    ) is False


def test_supported_working_hours_passes():

    guardrail = GroundingGuardrail()

    evidence = [
        {
            "text": (
                "Working hours are 9:30 AM to 6:00 PM "
                "Monday through Friday."
            )
        }
    ]

    answer = (
        "Employees work from 9:30 AM to 6:00 PM "
        "Monday through Friday."
    )

    assert guardrail.validate(
        answer=answer,
        evidence=evidence,
    ) is True


def test_contradictory_wfh_days_fail():

    guardrail = GroundingGuardrail()

    evidence = [
        {
            "text": (
                "Eligible employees may work from home "
                "up to 2 days per week."
            )
        }
    ]

    answer = (
        "Employees may work from home "
        "up to 5 days per week."
    )

    assert guardrail.validate(
        answer=answer,
        evidence=evidence,
    ) is False


def test_supported_leave_policy_passes():

    guardrail = GroundingGuardrail()

    evidence = [
        {
            "text": (
                "Full-time employees receive "
                "24 days of paid annual leave "
                "per calendar year."
            )
        }
    ]

    answer = (
        "Full-time employees receive "
        "24 days of paid annual leave per year."
    )

    assert guardrail.validate(
        answer=answer,
        evidence=evidence,
    ) is True


def test_unrelated_answer_fails():

    guardrail = GroundingGuardrail()

    evidence = [
        {
            "text": (
                "Working hours are 9:30 AM to 6:00 PM "
                "Monday through Friday."
            )
        }
    ]

    answer = (
        "Employees receive health insurance "
        "and retirement benefits."
    )

    assert guardrail.validate(
        answer=answer,
        evidence=evidence,
    ) is False

def test_mixed_supported_and_unsupported_claim_fails():

    guardrail = GroundingGuardrail()

    evidence = [
        {
            "text": (
                "Working hours are 9:30 AM to 6:00 PM "
                "Monday through Friday."
            )
        }
    ]

    answer = (
        "Employees work Monday through Friday "
        "and receive health insurance."
    )

    assert guardrail.validate(
        answer=answer,
        evidence=evidence,
    ) is False