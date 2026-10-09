from datetime import datetime, timedelta, timezone

import pytest

import app.security.user_repository as repository
from app.security.password import verify_password
from app.security.password_reset import (
    complete_password_reset,
    create_reset_token,
    hash_reset_token,
)
from app.security.password import hash_password, verify_password

@pytest.fixture
def isolated_database(tmp_path, monkeypatch):
    test_db = tmp_path / "password_reset_test.sqlite3"

    monkeypatch.setattr(repository, "DB_PATH", test_db)
    repository.initialize_database()

    repository.create_user(
        full_name="Reset Test User",
        username="resetuser",
        email="resetuser@example.com",
        password_hash=hash_password("OldStrongPassword123!"),
    )

    return repository


def test_reset_token_is_stored_as_hash(isolated_database):
    token = create_reset_token("resetuser@example.com")

    assert token is not None

    stored_token = isolated_database.get_connection().execute(
        """
        SELECT token_hash
        FROM password_reset_tokens
        """
    ).fetchone()

    assert stored_token is not None
    assert stored_token["token_hash"] == hash_reset_token(token)
    assert stored_token["token_hash"] != token


def test_password_reset_succeeds(isolated_database):
    token = create_reset_token("resetuser@example.com")

    assert token is not None

    assert complete_password_reset(
        token,
        "NewStrongPassword123!",
    )

    user = isolated_database.get_user_by_username("resetuser")

    assert verify_password(
        "NewStrongPassword123!",
        user["password_hash"],
    )


def test_reset_token_cannot_be_reused(isolated_database):
    token = create_reset_token("resetuser@example.com")

    assert token is not None

    assert complete_password_reset(
        token,
        "NewStrongPassword123!",
    )

    assert not complete_password_reset(
        token,
        "AnotherStrongPassword123!",
    )


def test_unknown_email_does_not_create_token(isolated_database):
    token = create_reset_token("unknown@example.com")

    assert token is None

    stored_tokens = isolated_database.get_connection().execute(
        "SELECT COUNT(*) FROM password_reset_tokens"
    ).fetchone()[0]

    assert stored_tokens == 0


def test_new_token_invalidates_previous_token(isolated_database):
    first_token = create_reset_token("resetuser@example.com")
    second_token = create_reset_token("resetuser@example.com")

    assert first_token is not None
    assert second_token is not None
    assert first_token != second_token

    assert not complete_password_reset(
        first_token,
        "NewStrongPassword123!",
    )

    assert complete_password_reset(
        second_token,
        "NewStrongPassword123!",
    )


def test_expired_token_is_rejected(isolated_database):
    token = create_reset_token("resetuser@example.com")

    assert token is not None

    with isolated_database.get_connection() as connection:
        connection.execute(
            """
            UPDATE password_reset_tokens
            SET expires_at = ?
            WHERE token_hash = ?
            """,
            (
                (
                    datetime.now(timezone.utc)
                    - timedelta(minutes=1)
                ).isoformat(),
                hash_reset_token(token),
            ),
        )

    assert not complete_password_reset(
        token,
        "NewStrongPassword123!",
    )