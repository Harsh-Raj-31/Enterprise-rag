import requests


class APIClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")

    def login(self, username: str, password: str) -> dict:
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={
                "username": username,
                "password": password,
            },
            timeout=30,
        )

        response.raise_for_status()
        return response.json()

    def query(
    self,
    token: str,
    query: str,
    url: str | None = None,
) -> dict:
        response = requests.post(
            f"{self.base_url}/query",
            headers={
                "Authorization": f"Bearer {token}",
            },
            json={
                "query": query,
                "url": url,
            },
            timeout=120,
        )

        if not response.ok:
            try:
                detail = response.json().get("detail")
            except ValueError:
                detail = None

            if detail:
                raise RuntimeError(detail)

            response.raise_for_status()

        return response.json()