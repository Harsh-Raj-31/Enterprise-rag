from app.guardrails.unauthorized_retrieval import (
    UnauthorizedRetrievalGuardrail,
)


def test_authorized_role_passes():

    guardrail = UnauthorizedRetrievalGuardrail()

    evidence = [
        {
            "text": "General employee policy.",
            "metadata": {
                "allowed_roles": [
                    "employee",
                    "manager",
                    "hr",
                    "admin",
                ]
            },
        }
    ]

    assert guardrail.validate(
        evidence=evidence,
        user_role="employee",
    ) is True


def test_unauthorized_role_fails():

    guardrail = UnauthorizedRetrievalGuardrail()

    evidence = [
        {
            "text": "Confidential HR information.",
            "metadata": {
                "allowed_roles": [
                    "hr",
                    "admin",
                ]
            },
        }
    ]

    assert guardrail.validate(
        evidence=evidence,
        user_role="employee",
    ) is False


def test_admin_can_access_admin_document():

    guardrail = UnauthorizedRetrievalGuardrail()

    evidence = [
        {
            "text": "Executive document.",
            "metadata": {
                "allowed_roles": [
                    "admin",
                ]
            },
        }
    ]

    assert guardrail.validate(
        evidence=evidence,
        user_role="admin",
    ) is True


def test_missing_access_metadata_does_not_break_current_sources():

    guardrail = UnauthorizedRetrievalGuardrail()

    evidence = [
        {
            "employee_id": 104,
            "name": "Ananya Singh",
            "department": "Engineering",
            "role": "AI Engineer",
        }
    ]

    assert guardrail.validate(
        evidence=evidence,
        user_role="hr",
    ) is True


def test_empty_evidence_passes():

    guardrail = UnauthorizedRetrievalGuardrail()

    assert guardrail.validate(
        evidence=[],
        user_role="employee",
    ) is True


def test_missing_user_role_blocks_restricted_evidence():

    guardrail = UnauthorizedRetrievalGuardrail()

    evidence = [
        {
            "text": "Confidential HR information.",
            "metadata": {
                "allowed_roles": [
                    "hr",
                    "admin",
                ]
            },
        }
    ]

    assert guardrail.validate(
        evidence=evidence,
        user_role=None,
    ) is False


def test_missing_user_role_allows_unrestricted_current_sources():

    guardrail = UnauthorizedRetrievalGuardrail()

    evidence = [
        {
            "employee_id": 104,
            "name": "Ananya Singh",
            "department": "Engineering",
            "role": "AI Engineer",
        }
    ]

    assert guardrail.validate(
        evidence=evidence,
        user_role=None,
    ) is True