from pathlib import Path


DEFAULT_DOCUMENT_ROLES = {
    "employee_policy.pdf": [
        "employee",
        "manager",
        "hr",
        "admin",
    ],
}


def get_document_roles(source: str) -> list[str]:
    """
    Return the roles allowed to access a document.
    """

    filename = Path(source).name

    roles = DEFAULT_DOCUMENT_ROLES.get(filename)

    if roles is None:
        raise ValueError(
            f"No access policy configured for document: {filename}"
        )

    return roles