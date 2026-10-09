import pytest
from fastapi.testclient import TestClient

import app.security.user_repository as repository
import app.api.auth as auth_api

from app.main import app
from app.security.password_reset import create_reset_token
from app.security.users import register_user


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db = tmp_path / "password_reset_api_test.sqlite3"

    monkeypatch.setattr(repository, "DB_PATH", test_db)
    repository.initialize_database()

    # Reset in-memory rate-limit state between tests.
    auth_api.forgot_password_limiter._requests.clear()
    auth_api.reset_password_limiter._requests.clear()

    with TestClient(app) as test_client:
        yield test_client


def create_test_user():
    return register_user(
        full_name="Test Employee",
        username="resetemployee",
        email="resetemployee@example.com",
        password="OriginalPassword123!",
    )


def test_forgot_password_returns_generic_message_for_unknown_email(client):
    response = client.post(
        "/auth/forgot-password",
        json={"email": "unknown@example.com"},
    )

    assert response.status_code == 200
    assert "If an account exists" in response.json()["message"]


def test_forgot_password_sends_email_without_exposing_token(
    client, monkeypatch
):
    create_test_user()
    captured = {}

    def fake_send_email(*, recipient_email, reset_token):
        captured["recipient_email"] = recipient_email
        captured["reset_token"] = reset_token

    monkeypatch.setattr(
        auth_api,
        "send_password_reset_email",
        fake_send_email,
    )

    response = client.post(
        "/auth/forgot-password",
        json={"email": "resetemployee@example.com"},
    )

    assert response.status_code == 200
    assert captured["recipient_email"] == "resetemployee@example.com"
    assert captured["reset_token"]
    assert captured["reset_token"] not in response.text


def test_forgot_password_invalidates_token_when_email_fails(
    client, monkeypatch
):
    user = create_test_user()
    captured = {}

    def failing_send_email(*, recipient_email, reset_token):
        captured["reset_token"] = reset_token
        raise RuntimeError("Simulated SMTP failure")

    monkeypatch.setattr(
        auth_api,
        "send_password_reset_email",
        failing_send_email,
    )

    response = client.post(
        "/auth/forgot-password",
        json={"email": user["email"]},
    )

    # The API returns the same generic response.
    assert response.status_code == 200
    assert "If an account exists" in response.json()["message"]

    # The token generated before the email failure must be invalidated.
    assert captured["reset_token"]

    reset_response = client.post(
        "/auth/reset-password",
        json={
            "token": captured["reset_token"],
            "new_password": "UpdatedPassword123!",
        },
    )

    assert reset_response.status_code == 400

def test_reset_password_changes_password(client):
    user = create_test_user()
    token = create_reset_token(user["email"])

    assert token

    response = client.post(
        "/auth/reset-password",
        json={
            "token": token,
            "new_password": "UpdatedPassword123!",
        },
    )

    assert response.status_code == 200
    assert "successfully" in response.json()["message"].lower()

    login_response = client.post(
        "/auth/login",
        json={
            "username": "resetemployee",
            "password": "UpdatedPassword123!",
        },
    )

    assert login_response.status_code == 200


def test_reset_password_rejects_reused_token(client):
    user = create_test_user()
    token = create_reset_token(user["email"])

    first_response = client.post(
        "/auth/reset-password",
        json={
            "token": token,
            "new_password": "UpdatedPassword123!",
        },
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/auth/reset-password",
        json={
            "token": token,
            "new_password": "AnotherPassword123!",
        },
    )

    assert second_response.status_code == 400


def test_reset_password_rejects_weak_password(client):
    user = create_test_user()
    token = create_reset_token(user["email"])

    response = client.post(
        "/auth/reset-password",
        json={
            "token": token,
            "new_password": "weakpassword",
        },
    )

    assert response.status_code == 422