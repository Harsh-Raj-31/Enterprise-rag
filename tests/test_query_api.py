from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def get_token(username: str, password: str) -> str:
    response = client.post(
        "/auth/login",
        json={
            "username": username,
            "password": password,
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def test_query_requires_authentication():
    response = client.post(
        "/query",
        json={
            "query": "How many annual leave days do employees receive?"
        },
    )

    assert response.status_code == 401


def test_employee_can_query_policy():
    token = get_token(
        "aarav",
        "employee123",
    )

    response = client.post(
        "/query",
        json={
            "query": "How many annual leave days do employees receive?"
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "24 days" in data["answer"]
    assert data["sources"]

    assert data["sources"][0]["source"] == "employee_policy.pdf"


def test_employee_cannot_access_employee_records():
    token = get_token(
        "aarav",
        "employee123",
    )

    response = client.post(
        "/query",
        json={
            "query": "Show me employee 104"
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 403


def test_hr_can_access_employee_records():
    token = get_token(
        "priya",
        "hr123",
    )

    response = client.post(
        "/query",
        json={
            "query": "Show me employee 104"
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "Ananya Singh" in data["answer"]
    assert data["sources"][0]["type"] == "database"
    assert data["sources"][0]["employee_id"] == 104