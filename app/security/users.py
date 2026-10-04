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


def authenticate_user(
    username: str,
    password: str,
) -> User | None:
    """
    Authenticate a user using the demo credential store.

    Returns the authenticated User or None if
    the credentials are invalid.
    """

    account = USERS.get(username)

    if account is None:
        return None

    if not verify_password(password, account["password_hash"]):
        return None

    return account["user"]