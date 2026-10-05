from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.api.query import cache_service
from app.cache.cache_key import build_cache_key


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


def test_second_identical_query_uses_cache():
    token = get_token(
        "aarav",
        "employee123",
    )

    query = {
        "query": "How many annual leave days do employees receive?"
    }

    cache_key = build_cache_key(
        query=query["query"],
        user_role="employee",
        user_id="EMP101",
    )

    cache_service.delete(cache_key)

    with patch(
        "app.api.query.graph_service.invoke"
    ) as mock_invoke:

        mock_invoke.return_value = {
            "answer": "Full-time employees receive 24 days.",
            "sources": [
                {
                    "source": "employee_policy.pdf",
                    "page": 2,
                }
            ],
        }

        response1 = client.post(
            "/query",
            json=query,
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response1.status_code == 200
        assert mock_invoke.call_count == 1

        response2 = client.post(
            "/query",
            json=query,
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response2.status_code == 200

        # Second request should come from Redis.
        assert mock_invoke.call_count == 1

        assert response2.json() == response1.json()

    cache_service.delete(cache_key)


def test_cache_is_isolated_by_user_role():
    employee_token = get_token(
        "aarav",
        "employee123",
    )

    hr_token = get_token(
        "priya",
        "hr123",
    )

    query = {
        "query": "How many annual leave days do employees receive?"
    }

    employee_key = build_cache_key(
        query=query["query"],
        user_role="employee",
        user_id="EMP101",
    )

    hr_key = build_cache_key(
        query=query["query"],
        user_role="hr",
        user_id="HR201",
    )

    # Start clean.
    cache_service.delete(employee_key)
    cache_service.delete(hr_key)

    with patch(
        "app.api.query.graph_service.invoke"
    ) as mock_invoke:

        mock_invoke.return_value = {
            "answer": "Full-time employees receive 24 days.",
            "sources": [
                {
                    "source": "employee_policy.pdf",
                    "page": 2,
                }
            ],
        }

        # Employee request creates employee-specific cache entry.
        employee_response = client.post(
            "/query",
            json=query,
            headers={
                "Authorization": f"Bearer {employee_token}",
            },
        )

        assert employee_response.status_code == 200
        assert mock_invoke.call_count == 1

        # HR has a different security context, so it must not
        # reuse the employee's cached response.
        hr_response = client.post(
            "/query",
            json=query,
            headers={
                "Authorization": f"Bearer {hr_token}",
            },
        )

        assert hr_response.status_code == 200
        assert mock_invoke.call_count == 2

    assert employee_key != hr_key

    cache_service.delete(employee_key)
    cache_service.delete(hr_key)   

def test_unauthorized_query_is_not_cached():
    token = get_token(
        "aarav",
        "employee123",
    )

    query = {
        "query": "Show me employee 104"
    }

    cache_key = build_cache_key(
        query=query["query"],
        user_role="employee",
        user_id="EMP101",
    )

    # Ensure no old cache entry exists.
    cache_service.delete(cache_key)

    with patch(
        "app.api.query.graph_service.invoke"
    ) as mock_invoke:

        mock_invoke.side_effect = PermissionError(
            "You are not authorized to access this resource."
        )

        response = client.post(
            "/query",
            json=query,
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 403

        # The failed request must not create a cache entry.
        assert cache_service.get(cache_key) is None

    cache_service.delete(cache_key)    