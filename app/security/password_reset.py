import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from app.security.user_repository import (
    create_password_reset_token,
    get_user_by_email,
    reset_password_with_token,
)
from app.security.password import hash_password


RESET_TOKEN_TTL_MINUTES = 30


def hash_reset_token(token: str) -> str:
    """Hash a reset token before storing or looking it up."""

    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_reset_token(email: str) -> str | None:
    """
    Create a reset token for an existing email address.

    Returns the raw token for the email-delivery layer.
    Only its SHA-256 hash is stored in the database.
    """

    user = get_user_by_email(email)

    if user is None:
        return None

    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_reset_token(raw_token)

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(minutes=RESET_TOKEN_TTL_MINUTES)
    ).isoformat()

    create_password_reset_token(
        user_id=user["user_id"],
        token_hash=token_hash,
        expires_at=expires_at,
    )

    return raw_token


def complete_password_reset(
    token: str,
    new_password: str,
) -> bool:
    """Change the password using a valid, unused reset token."""

    if not token or not new_password:
        return False

    token_hash = hash_reset_token(token)
    new_password_hash = hash_password(new_password)

    return reset_password_with_token(
        token_hash=token_hash,
        password_hash=new_password_hash,
    )