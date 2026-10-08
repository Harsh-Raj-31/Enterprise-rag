from app.security.models import RolePermissions


ROLE_PERMISSIONS = {
    "employee": RolePermissions(
        role="employee",
        allowed_sources=frozenset({
            "hr_policy",
            "general_policy",

        }),
        allowed_actions=frozenset({
            "query",
            "ingest",
        }),
    ),

    "manager": RolePermissions(
        role="manager",
        allowed_sources=frozenset({
            "hr_policy",
            "general_policy",
            "team_records",
        }),
        allowed_actions=frozenset({
            "query",
            "ingest",
        }),
    ),

    "hr": RolePermissions(
        role="hr",
        allowed_sources=frozenset({
            "hr_policy",
            "general_policy",
            "employee_records",
            "salary_database",
        }),
        allowed_actions=frozenset({
            "query",
            "ingest",
        }),
    ),

    "admin": RolePermissions(
        role="admin",
        allowed_sources=frozenset({
            "hr_policy",
            "general_policy",
            "team_records",
            "employee_records",
            "salary_database",
            "executive_documents",
        }),
        allowed_actions=frozenset({
            "query",
            "ingest",
            "delete",
        }),
    ),
}


def get_role_permissions(role: str) -> RolePermissions:
    """
    Return permissions assigned to a role.
    """

    role = role.strip().lower()

    if role not in ROLE_PERMISSIONS:
        raise ValueError(
            f"Unknown role: {role}"
        )

    return ROLE_PERMISSIONS[role]

ROLE_ASSIGNMENT_POLICY = {
    "employee": frozenset({"employee"}),
    "manager": frozenset({"employee", "manager"}),
    "hr": frozenset({"employee", "manager", "hr"}),
    "admin": frozenset({"employee", "manager", "hr", "admin"}),
}


def validate_role_assignment(
    user_role: str,
    requested_roles: list[str] | None,
) -> list[str]:
    """
    Validate that a user can assign the requested access roles.
    """

    if requested_roles is None:
        requested_roles = [user_role]

    normalized_roles = {
        role.strip().lower()
        for role in requested_roles
        if role and role.strip()
    }

    if not normalized_roles:
        raise ValueError(
            "At least one valid role must be provided."
        )

    supported_roles = {
        "employee",
        "manager",
        "hr",
        "admin",
    }

    invalid_roles = normalized_roles - supported_roles

    if invalid_roles:
        raise ValueError(
            f"Invalid roles requested: {sorted(invalid_roles)}"
        )

    user_role = user_role.strip().lower()

    if user_role not in ROLE_ASSIGNMENT_POLICY:
        raise PermissionError(
            f"Unknown user role: {user_role}"
        )

    allowed_roles = ROLE_ASSIGNMENT_POLICY[user_role]

    unauthorized_roles = normalized_roles - allowed_roles

    if unauthorized_roles:
        raise PermissionError(
            f"Role '{user_role}' cannot assign access to: "
            f"{sorted(unauthorized_roles)}"
        )

    return sorted(normalized_roles)
