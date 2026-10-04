from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.security.rate_limiter import RateLimiter


def create_test_app():
    app = FastAPI()

    rate_limiter = RateLimiter(
        max_requests=2,
        window_seconds=60,
    )

    @app.middleware("http")
    async def rate_limit_middleware(request, call_next):
        excluded_paths = {
            "/",
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
        }

        if request.url.path in excluded_paths:
            return await call_next(request)

        client_key = (
            request.client.host
            if request.client
            else "unknown"
        )

        if not rate_limiter.is_allowed(client_key):
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=429,
                content={
                    "detail": (
                        "Too many requests. "
                        "Please try again later."
                    )
                },
                headers={"Retry-After": "60"},
            )

        return await call_next(request)

    @app.get("/protected")
    def protected():
        return {"status": "ok"}

    @app.get("/health")
    def health():
        return {"status": "healthy"}

    return app


def test_rate_limit_returns_429():
    app = create_test_app()
    client = TestClient(app)

    assert client.get("/protected").status_code == 200
    assert client.get("/protected").status_code == 200

    response = client.get("/protected")

    assert response.status_code == 429
    assert response.json()["detail"] == (
        "Too many requests. Please try again later."
    )
    assert response.headers["Retry-After"] == "60"


def test_health_endpoint_is_not_rate_limited():
    app = create_test_app()
    client = TestClient(app)

    # Exhaust the protected endpoint limit.
    client.get("/protected")
    client.get("/protected")
    assert client.get("/protected").status_code == 429

    # Health remains available.
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}