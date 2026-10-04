from app.security.models import User


def add_access_metadata(
    metadata: dict,
    allowed_roles: list[str],
) -> dict:
    """
    Add role-based access information to document metadata.
    """

    if not allowed_roles:
        raise ValueError(
            "allowed_roles cannot be empty."
        )

    normalized_roles = {
        role.strip().lower()
        for role in allowed_roles
        if role.strip()
    }

    if not normalized_roles:
        raise ValueError(
            "allowed_roles must contain valid roles."
        )

    updated_metadata = metadata.copy()

    updated_metadata["allowed_roles"] = sorted(
        normalized_roles
    )

    return updated_metadata


def user_can_access_document(
    user: User,
    metadata: dict,
) -> bool:
    """
    Check whether a user can access a document
    based on its allowed_roles metadata.
    """

    allowed_roles = metadata.get(
        "allowed_roles",
        [],
    )

    return user.role.lower() in {
        role.lower()
        for role in allowed_roles
    }