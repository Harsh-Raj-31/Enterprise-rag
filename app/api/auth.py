from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.security.auth import login


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post(
    "/login",
    response_model=LoginResponse,
)
def login_endpoint(request: LoginRequest):

    try:
        token = login(
            username=request.username,
            password=request.password,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=401,
            detail=str(exc),
        ) from exc

    return LoginResponse(
        access_token=token,
    )