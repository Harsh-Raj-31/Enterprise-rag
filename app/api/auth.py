from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.security.auth import decode_access_token, login


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
    username: str
    role: str


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

    user = decode_access_token(token)

    return LoginResponse(
        access_token=token,
        username=user.username,
        role=user.role,
    )
