from app.security.models import RolePermissions


ROLE_PERMISSIONS = {
    "employee": RolePermissions(
        role="employee",
        allowed_sources=frozenset({
            "hr_policy",
            "general_policy",
        }),
    ),

    "manager": RolePermissions(
        role="manager",
        allowed_sources=frozenset({
            "hr_policy",
            "general_policy",
            "team_records",
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