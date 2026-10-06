import logging
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.security.dependencies import get_current_user
from app.security.models import User
from app.services.graph_service import GraphService
from app.security.audit import audit_event
from app.cache.cache_key import build_cache_key
from app.cache.cache_service import CacheService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/query",
    tags=["Query"],
)


class QueryRequest(BaseModel):
    query: str
    url: str | None = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]


graph_service = GraphService()
cache_service = CacheService()


@router.post(
    "",
    response_model=QueryResponse,
)
def query_endpoint(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
):
    cache_key = build_cache_key(
        query=request.query,
        user_role=current_user.role,
        user_id=current_user.user_id,
        url=request.url,
    )

    cached_response = cache_service.get(cache_key)

    if cached_response:
        logger.info(
            "CACHE HIT | role=%s | key=%s",
            current_user.role,
            cache_key,
        )

        return json.loads(cached_response)

    logger.info(
        "CACHE MISS | role=%s | key=%s",
        current_user.role,
        cache_key,
    )

    try:
        result = graph_service.invoke(
            query=request.query,
            user_role=current_user.role,
            url=request.url,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc        

    except PermissionError as exc:
        audit_event(
            user_id=current_user.user_id,
            username=current_user.username,
            role=current_user.role,
            action="query",
            resource="knowledge_base",
            status="denied",
            details={
                "reason": "permission_denied",
            },
        )

        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc

    response = {
        "answer": result["answer"],
        "sources": result["sources"],
    }

    cache_service.set(
        key=cache_key,
        value=json.dumps(response),
        ttl=300,
    )

    logger.info(
        "CACHE SET | role=%s | ttl=%s | key=%s",
        current_user.role,
        300,
        cache_key,
    )

    audit_event(
        user_id=current_user.user_id,
        username=current_user.username,
        role=current_user.role,
        action="query",
        resource="knowledge_base",
        status="allowed",
        details={
            "route": result.get(
                "route",
                "unknown",
            ),
        },
    )

    return response
