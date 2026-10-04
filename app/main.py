from fastapi import FastAPI
from app.api.auth import router as auth_router
from fastapi import Depends
from app.security.dependencies import get_current_user
from app.security.models import User
from app.api.query import router as query_router
from fastapi import Request
from fastapi.responses import JSONResponse

from app.security.rate_limiter import RateLimiter

app = FastAPI(
    title="Enterprise Knowledge Base & RAG",
    description="Enterprise-ready Retrieval-Augmented Generation system",
    version="1.0.0"
)
rate_limiter = RateLimiter(
    max_requests=60,
    window_seconds=60,
)
app.include_router(auth_router)
app.include_router(query_router)

@app.get("/")
def root():
    return {
        "message": "Enterprise RAG API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/protected")
def protected_endpoint(
    current_user: User = Depends(get_current_user),
):
    return {
        "message": "You are authenticated",
        "user_id": current_user.user_id,
        "username": current_user.username,
        "role": current_user.role,
    }


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Keep health checks and API documentation available.
    excluded_paths = {
        "/",
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
    }

    if request.url.path in excluded_paths:
        return await call_next(request)

    # Prefer authenticated user identity when available.
    # Fall back to client IP for unauthenticated requests.
    client_key = request.client.host if request.client else "unknown"

    if not rate_limiter.is_allowed(client_key):
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Too many requests. Please try again later."
            },
            headers={
                "Retry-After": "60",
            },
        )

    return await call_next(request)


# cd C:\Projects\enterprise-rag
# .\.venv\Scripts\Activate.ps1
# python -m streamlit run app\ui\streamlit_app.py


# Test commands:
# python -m tests.test_pdf_loader
# python -m tests.test_chunker
# python -m tests.test_vector_store
# python -m tests.test_retriever
# python -m tests.test_keyword_retriever
# python -m tests.test_hybrid_retriever
# python -m tests.test_reranker
# python -m tests.test_llm_service
# python -m tests.test_rag_service