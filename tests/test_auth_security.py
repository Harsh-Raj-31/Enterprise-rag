from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.security.auth import (
    JWT_ALGORITHM,
    JWT_SECRET,
    create_access_token,
    decode_access_token,
)
from app.security.models import User


def test_valid_token():
    user = User(
        user_id="U001",
        username="aarav",
        role="employee",
    )

    token = create_access_token(user)
    decoded_user = decode_access_token(token)

    assert decoded_user.user_id == "U001"
    assert decoded_user.username == "aarav"
    assert decoded_user.role == "employee"


def test_invalid_token():
    with pytest.raises(ValueError, match="Invalid or expired access token"):
        decode_access_token("this-is-not-a-valid-jwt")


def test_expired_token():
    now = datetime.now(timezone.utc)

    payload = {
        "sub": "U001",
        "username": "aarav",
        "role": "employee",
        "iat": now - timedelta(hours=2),
        "exp": now - timedelta(hours=1),
    }

    expired_token = jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )

    with pytest.raises(ValueError, match="Invalid or expired access token"):
        decode_access_token(expired_token)


def test_wrong_secret_token():
    now = datetime.now(timezone.utc)

    payload = {
        "sub": "U001",
        "username": "aarav",
        "role": "employee",
        "iat": now,
        "exp": now + timedelta(hours=1),
    }

    token = jwt.encode(
        payload,
        "definitely-not-the-real-secret-32-bytes-minimum",
        algorithm=JWT_ALGORITHM,
    )

    with pytest.raises(ValueError, match="Invalid or expired access token"):
        decode_access_token(token)