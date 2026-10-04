from app.security.models import User


def filter_documents_by_role(
    documents: list[dict],
    user: User,
) -> list[dict]:
    """
    Return only documents that the user's role
    is authorized to access.
    """

    filtered_documents = []

    for document in documents:

        metadata = document.get("metadata", {})

        allowed_roles = metadata.get(
            "allowed_roles",
            [],
        )

        normalized_roles = {
            role.lower()
            for role in allowed_roles
        }

        if user.role.lower() in normalized_roles:
            filtered_documents.append(document)

    return filtered_documents