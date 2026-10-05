import hashlib


def build_cache_key(
    query: str,
    user_role: str | None,
    user_id: str | None,
) -> str:
    normalized_query = " ".join(query.strip().lower().split())
    normalized_role = user_role.strip().lower() if user_role else "anonymous"
    normalized_user_id = user_id.strip().lower() if user_id else "anonymous"

    query_hash = hashlib.sha256(
        normalized_query.encode("utf-8")
    ).hexdigest()

    return (
        f"rag:{normalized_role}:"
        f"{normalized_user_id}:"
        f"{query_hash}"
    )