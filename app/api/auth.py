import re

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field

from app.security.audit import audit_event
from app.security.auth import decode_access_token, login
from app.security.email_service import send_password_reset_email
from app.security.password_reset import (
    complete_password_reset,
    create_reset_token,
    hash_reset_token,
)
from app.security.password_reset_limiter import (
    forgot_password_limiter,
    reset_password_limiter,
)
from app.security.user_repository import invalidate_password_reset_token
from app.security.users import register_user


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# ============================================================
# LOGIN
# ============================================================

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
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    user = decode_access_token(token)

    return LoginResponse(
        access_token=token,
        username=user.username,
        role=user.role,
    )


# ============================================================
# SIGN UP
# ============================================================

class SignupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(min_length=2, max_length=100)
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=12, max_length=72)


class SignupResponse(BaseModel):
    message: str
    username: str
    role: str


def validate_signup_request(request: SignupRequest) -> None:
    """Validate signup fields before creating an account."""

    if not request.full_name.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Full name cannot be empty.",
        )

    if not re.fullmatch(
        r"[A-Za-z0-9_.-]+",
        request.username.strip(),
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                "Username can contain only letters, numbers, "
                "underscores, periods, and hyphens."
            ),
        )

    if not re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+",
        request.email.strip(),
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Enter a valid email address.",
        )

    # bcrypt has a 72-byte input limit.
    if len(request.password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Password must not exceed 72 UTF-8 bytes.",
        )


@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
)
def signup_endpoint(request: SignupRequest):
    validate_signup_request(request)

    try:
        user = register_user(
            full_name=request.full_name,
            username=request.username,
            email=request.email,
            password=request.password,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return SignupResponse(
        message="Account created successfully.",
        username=user["username"],
        role=user["role"],
    )


# ============================================================
# PASSWORD RESET REQUEST MODELS
# ============================================================

class ForgotPasswordRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254)


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    new_password: str = Field(min_length=12, max_length=72)


class MessageResponse(BaseModel):
    message: str


# ============================================================
# PASSWORD RESET AUDIT
# ============================================================

def audit_password_reset_event(
    *,
    action: str,
    event_status: str,
    details: dict | None = None,
) -> None:
    """Record password-reset events without exposing credentials."""

    audit_event(
        user_id="anonymous",
        username="anonymous",
        role="anonymous",
        action=action,
        resource="password",
        status=event_status,
        details=details or {},
    )


# ============================================================
# FORGOT PASSWORD
# ============================================================

@router.post(
    "/forgot-password",
    response_model=MessageResponse,
)
def forgot_password_endpoint(
    request: ForgotPasswordRequest,
    http_request: Request,
):
    client_ip = (
        http_request.client.host
        if http_request.client
        else "unknown"
    )

    if not forgot_password_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "Too many password-reset requests. "
                "Please try again later."
            ),
        )

    # Keep the public response identical for known and unknown emails.
    generic_message = (
        "If an account exists for that email address, "
        "a password-reset link will be sent."
    )

    token = create_reset_token(request.email)

    if token is None:
        audit_password_reset_event(
            action="password_reset_requested",
            event_status="accepted",
        )

        return MessageResponse(message=generic_message)

    try:
        send_password_reset_email(
            recipient_email=request.email,
            reset_token=token,
        )

    except Exception:
        # Do not leave an unusable reset link active after email failure.
        invalidate_password_reset_token(
            hash_reset_token(token)
        )

        audit_password_reset_event(
            action="password_reset_email",
            event_status="failed",
        )

        # Avoid revealing whether the email belongs to an account.
        return MessageResponse(message=generic_message)

    audit_password_reset_event(
        action="password_reset_email",
        event_status="sent",
    )

    return MessageResponse(message=generic_message)


# ============================================================
# RESET PASSWORD
# ============================================================

@router.post(
    "/reset-password",
    response_model=MessageResponse,
)
def reset_password_endpoint(
    request: ResetPasswordRequest,
    http_request: Request,
):
    client_ip = (
        http_request.client.host
        if http_request.client
        else "unknown"
    )

    if not reset_password_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "Too many password-reset attempts. "
                "Please try again later."
            ),
        )

    # Enforce bcrypt's byte limit, including for multibyte characters.
    if len(request.new_password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Password must not exceed 72 UTF-8 bytes.",
        )

    if not any(char.isupper() for char in request.new_password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Password must contain an uppercase letter.",
        )

    if not any(char.islower() for char in request.new_password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Password must contain a lowercase letter.",
        )

    if not any(char.isdigit() for char in request.new_password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Password must contain a number.",
        )

    try:
        reset_successful = complete_password_reset(
            token=request.token,
            new_password=request.new_password,
        )

    except Exception as exc:
        audit_password_reset_event(
            action="password_reset_completed",
            event_status="failed",
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset could not be completed.",
        ) from exc

    if not reset_successful:
        audit_password_reset_event(
            action="password_reset_completed",
            event_status="rejected",
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The reset link is invalid or expired.",
        )

    audit_password_reset_event(
        action="password_reset_completed",
        event_status="success",
    )

    return MessageResponse(
        message="Password reset successfully. You can now log in."
    )
