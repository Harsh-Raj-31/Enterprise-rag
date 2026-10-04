from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.security.dependencies import get_current_user
from app.security.models import User
from app.services.graph_service import GraphService
from app.security.audit import audit_event


router = APIRouter(
    prefix="/query",
    tags=["Query"],
)


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]


graph_service = GraphService()


@router.post(
    "",
    response_model=QueryResponse,
)
def query_endpoint(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        result = graph_service.invoke(
            query=request.query,
            user_role=current_user.role,
        )

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

    audit_event(
        user_id=current_user.user_id,
        username=current_user.username,
        role=current_user.role,
        action="query",
        resource="knowledge_base",
        status="allowed",
        details={
            "route": result.get("route", "unknown"),
        },
    )

    return {
        "answer": result["answer"],
        "sources": result["sources"],
    }