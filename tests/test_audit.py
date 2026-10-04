import logging

from app.security.audit import audit_event
from unittest.mock import patch

from app.security.models import User


def test_audit_event_logs_security_event(caplog):
    with caplog.at_level(
        logging.INFO,
        logger="enterprise_rag.audit",
    ):
        audit_event(
            user_id="EMP101",
            username="aarav",
            role="employee",
            action="query",
            resource="hr_policy",
            status="allowed",
            details={"route": "PDF"},
        )

    assert "AUDIT_EVENT" in caplog.text
    assert "EMP101" in caplog.text
    assert "aarav" in caplog.text
    assert "employee" in caplog.text
    assert "hr_policy" in caplog.text
    assert "allowed" in caplog.text


def test_query_audit_event_for_allowed_access():
    from app.api.query import query_endpoint, QueryRequest

    user = User(
        user_id="EMP101",
        username="aarav",
        role="employee",
    )

    fake_result = {
        "answer": "Employees receive 24 days of annual leave.",
        "sources": [],
    }

    with patch(
        "app.api.query.graph_service.invoke",
        return_value=fake_result,
    ), patch(
        "app.api.query.audit_event"
    ) as mock_audit:

        result = query_endpoint(
            request=QueryRequest(
                query="How many annual leave days do employees receive?"
            ),
            current_user=user,
        )

    assert result["answer"].startswith(
        "Employees receive 24 days"
    )

    mock_audit.assert_called_once_with(
        user_id="EMP101",
        username="aarav",
        role="employee",
        action="query",
        resource="knowledge_base",
        status="allowed",
        details={"route": "unknown"},
    )


def test_query_audit_event_for_denied_access():
    from app.api.query import query_endpoint, QueryRequest

    user = User(
        user_id="EMP101",
        username="aarav",
        role="employee",
    )

    with patch(
        "app.api.query.graph_service.invoke",
        side_effect=PermissionError(
            "Access denied."
        ),
    ), patch(
        "app.api.query.audit_event"
    ) as mock_audit:

        try:
            query_endpoint(
                request=QueryRequest(
                    query="Show me employee records"
                ),
                current_user=user,
            )
        except Exception as exc:
            assert getattr(exc, "status_code", None) == 403

    mock_audit.assert_called_once_with(
        user_id="EMP101",
        username="aarav",
        role="employee",
        action="query",
        resource="knowledge_base",
        status="denied",
        details={"reason": "permission_denied"},
    )
