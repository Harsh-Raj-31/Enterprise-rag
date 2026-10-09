import pytest
from fastapi.testclient import TestClient

import app.security.user_repository as repository
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db = tmp_path / "signup_api_test.sqlite3"

    monkeypatch.setattr(repository, "DB_PATH", test_db)
    repository.initialize_database()

    with TestClient(app) as test_client:
        yield test_client


def valid_signup_payload():
    return {
        "full_name": "Test Employee",
        "username": "newemployee",
        "email": "newemployee@example.com",
        "password": "StrongTestPassword123!",
    }


def test_signup_creates_employee_account(client):
    response = client.post(
        "/auth/signup",
        json=valid_signup_payload(),
    )

    assert response.status_code == 201
    assert response.json()["username"] == "newemployee"
    assert response.json()["role"] == "employee"


def test_signup_rejects_duplicate_username(client):
    payload = valid_signup_payload()

    first_response = client.post("/auth/signup", json=payload)
    assert first_response.status_code == 201

    duplicate_payload = {
        **payload,
        "email": "another@example.com",
    }

    response = client.post(
        "/auth/signup",
        json=duplicate_payload,
    )

    assert response.status_code == 409


def test_signup_rejects_duplicate_email(client):
    payload = valid_signup_payload()

    first_response = client.post("/auth/signup", json=payload)
    assert first_response.status_code == 201

    duplicate_payload = {
        **payload,
        "username": "anotheremployee",
    }

    response = client.post(
        "/auth/signup",
        json=duplicate_payload,
    )

    assert response.status_code == 409


def test_signup_rejects_privileged_role(client):
    payload = {
        **valid_signup_payload(),
        "role": "admin",
    }

    response = client.post("/auth/signup", json=payload)

    assert response.status_code == 422


def test_signup_rejects_weak_password(client):
    payload = {
        **valid_signup_payload(),
        "password": "short",
    }

    response = client.post("/auth/signup", json=payload)

    assert response.status_code == 422


def test_signup_rejects_invalid_email(client):
    payload = {
        **valid_signup_payload(),
        "email": "not-an-email",
    }

    response = client.post("/auth/signup", json=payload)

    assert response.status_code == 422


def test_new_account_can_login(client):
    payload = valid_signup_payload()

    signup_response = client.post("/auth/signup", json=payload)
    assert signup_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "username": payload["username"],
            "password": payload["password"],
        },
    )

    assert login_response.status_code == 200
    assert login_response.json()["username"] == payload["username"]
    assert login_response.json()["role"] == "employee"
    assert login_response.json()["access_token"]