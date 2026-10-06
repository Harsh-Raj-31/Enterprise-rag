import hashlib


def build_cache_key(
    query: str,
    user_role: str | None,
    user_id: str | None,
    url: str | None = None,
) -> str:
    normalized_query = " ".join(query.strip().lower().split())
    normalized_role = user_role.strip().lower() if user_role else "anonymous"
    normalized_user_id = user_id.strip().lower() if user_id else "anonymous"
    normalized_url = url.strip().lower() if url else ""

    cache_input = (
        f"{normalized_query}|"
        f"{normalized_url}"
    )

    query_hash = hashlib.sha256(
        cache_input.encode("utf-8")
    ).hexdigest()

    return (
        f"rag:{normalized_role}:"
        f"{normalized_user_id}:"
        f"{query_hash}"
    )