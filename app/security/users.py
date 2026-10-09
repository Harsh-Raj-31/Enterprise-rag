import sqlite3
from app.security.user_repository import (
    create_user,
    get_user_by_email,
    get_user_by_username,
)

from app.security.models import User
from app.security.password import hash_password, verify_password


USERS = {
    "aarav": {
        "password_hash": hash_password("employee123"),
        "user": User(
            user_id="EMP101",
            username="aarav",
            role="employee",
        ),
    },
    "priya": {
        "password_hash": hash_password("hr123"),
        "user": User(
            user_id="HR201",
            username="priya",
            role="hr",
        ),
    },
    "rohan": {
        "password_hash": hash_password("manager123"),
        "user": User(
            user_id="MGR301",
            username="rohan",
            role="manager",
        ),
    },
    "admin": {
        "password_hash": hash_password("admin123"),
        "user": User(
            user_id="ADM001",
            username="admin",
            role="admin",
        ),
    },
}


def authenticate_user(username: str, password: str) -> User | None:
    """Authenticate a persistent user or an existing demo account."""

    # First, check persistent SQLite accounts.
    account = get_user_by_username(username)

    if account is not None:
        if not verify_password(password, account["password_hash"]):
            return None

        return User(
            user_id=account["user_id"],
            username=account["username"],
            role=account["role"],
        )

    # Preserve compatibility with the existing demo accounts.
    account = USERS.get(username)

    if account is None:
        return None

    if not verify_password(password, account["password_hash"]):
        return None

    return account["user"]



def register_user(
    full_name: str,
    username: str,
    email: str,
    password: str,
) -> dict:
    """Register a new user with the default employee role."""

    normalized_username = username.strip().lower()
    normalized_email = email.strip().lower()

    # Prevent registration using existing demo usernames.
    if normalized_username in {name.lower() for name in USERS}:
        raise ValueError("Username is already registered.")

    # Check for existing persistent accounts.
    if get_user_by_username(normalized_username):
        raise ValueError("Username is already registered.")

    if get_user_by_email(normalized_email):
        raise ValueError("Email is already registered.")

    password_hash = hash_password(password)

    try:
        return create_user(
            full_name=full_name,
            username=normalized_username,
            email=normalized_email,
            password_hash=password_hash,
        )
    except sqlite3.IntegrityError as exc:
        # Database uniqueness constraints protect against concurrent requests.
        raise ValueError(
            "Username or email is already registered."
        ) from exc