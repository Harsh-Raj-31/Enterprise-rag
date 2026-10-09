import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv

from app.security.models import User
from app.security.users import authenticate_user
from app.security.audit import audit_event


load_dotenv()


JWT_SECRET = os.getenv("JWT_SECRET")

if not JWT_SECRET:
    raise RuntimeError(
        "JWT_SECRET is not configured. Set JWT_SECRET in the environment."
    )

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 60


def create_access_token(user: User) -> str:
    """
    Create a JWT access token for an authenticated user.
    """

    now = datetime.now(timezone.utc)

    payload = {
        "sub": user.user_id,
        "username": user.username,
        "role": user.role,
        "iat": now,
        "exp": now + timedelta(
            minutes=JWT_EXPIRATION_MINUTES
        ),
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> User:
    """
    Validate a JWT access token and reconstruct the user.
    """

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )

    except jwt.InvalidTokenError as exc:
        raise ValueError(
            "Invalid or expired access token."
        ) from exc

    user_id = payload.get("sub")
    username = payload.get("username")
    role = payload.get("role")

    if not user_id or not username or not role:
        raise ValueError(
            "Access token is missing required user information."
        )

    return User(
        user_id=user_id,
        username=username,
        role=role,
    )


def login(username, password):
    user = authenticate_user(
        username=username,
        password=password,
    )

    if user is None:
        audit_event(
            user_id="unknown",
            username=username,
            role="unknown",
            action="login",
            resource="authentication",
            status="failure",
        )

        raise ValueError("Invalid username or password.")

    audit_event(
        user_id=user.user_id,
        username=user.username,
        role=user.role,
        action="login",
        resource="authentication",
        status="success",
    )

    return create_access_token(user)