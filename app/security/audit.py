import logging
from typing import Any


audit_logger = logging.getLogger("enterprise_rag.audit")


def audit_event(
    *,
    user_id: str,
    username: str,
    role: str,
    action: str,
    resource: str,
    status: str,
    details: dict[str, Any] | None = None,
) -> None:
    """
    Record a security-relevant audit event.

    Sensitive values such as passwords and tokens must never
    be included in details.
    """

    event = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "action": action,
        "resource": resource,
        "status": status,
        "details": details or {},
    }

    audit_logger.info("AUDIT_EVENT %s", event)