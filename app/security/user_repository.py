import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


DEFAULT_DB_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "auth"
    / "users.sqlite3"
)

DB_PATH = Path(
    os.getenv("AUTH_DB_PATH", str(DEFAULT_DB_PATH))
).resolve()


def get_connection() -> sqlite3.Connection:
    """Create a connection to the persistent user database."""

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        str(DB_PATH),
        timeout=10,
    )

    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def initialize_database() -> None:
    """Create the users table and its uniqueness constraints."""

    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                username TEXT NOT NULL COLLATE NOCASE UNIQUE,
                email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'employee'
                    CHECK (
                        role IN (
                            'employee',
                            'manager',
                            'hr',
                            'admin'
                        )
                    ),
                created_at TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                token_hash TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used_at TEXT,
                FOREIGN KEY (user_id)
                    REFERENCES users(user_id)
                    ON DELETE CASCADE
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_reset_tokens_user_id
            ON password_reset_tokens(user_id)
            """
        )        


def create_user(
    full_name: str,
    username: str,
    email: str,
    password_hash: str,
) -> dict:
    """
    Persist a new user account.

    Public registration always creates an employee account.
    The role is deliberately not accepted as an argument.
    """

    user_id = f"USR-{uuid4().hex}"

    created_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO users (
                user_id,
                full_name,
                username,
                email,
                password_hash,
                role,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, 'employee', ?)
            """,
            (
                user_id,
                full_name.strip(),
                username.strip(),
                email.strip().lower(),
                password_hash,
                created_at,
            ),
        )

        if cursor.rowcount != 1:
            raise RuntimeError("The user account was not created.")

    return get_user_by_username(username)


def get_user_by_username(username: str) -> dict | None:
    """Find a user by username, ignoring case."""

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            """,
            (username.strip(),),
        ).fetchone()

    return dict(row) if row else None


def get_user_by_email(email: str) -> dict | None:
    """Find a user by email address, ignoring case."""

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email.strip(),),
        ).fetchone()

    return dict(row) if row else None


def update_password_hash(
    user_id: str,
    password_hash: str,
) -> bool:
    """Replace a user's password hash."""

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE users
            SET password_hash = ?
            WHERE user_id = ?
            """,
            (password_hash, user_id),
        )

    return cursor.rowcount == 1

def create_password_reset_token(
    user_id: str,
    token_hash: str,
    expires_at: str,
) -> None:
    """Store a hashed reset token and invalidate previous unused tokens."""

    created_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE password_reset_tokens
            SET used_at = ?
            WHERE user_id = ?
              AND used_at IS NULL
            """,
            (created_at, user_id),
        )

        connection.execute(
            """
            INSERT INTO password_reset_tokens (
                token_hash,
                user_id,
                created_at,
                expires_at,
                used_at
            )
            VALUES (?, ?, ?, ?, NULL)
            """,
            (token_hash, user_id, created_at, expires_at),
        )

def reset_password_with_token(
    token_hash: str,
    password_hash: str,
) -> bool:
    """
    Reset a password using a valid, unused, unexpired token.

    Token consumption and password update occur in one transaction.
    """

    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        token = connection.execute(
            """
            SELECT user_id
            FROM password_reset_tokens
            WHERE token_hash = ?
              AND used_at IS NULL
              AND expires_at > ?
            """,
            (token_hash, now),
        ).fetchone()

        if token is None:
            return False

        cursor = connection.execute(
            """
            UPDATE password_reset_tokens
            SET used_at = ?
            WHERE token_hash = ?
              AND used_at IS NULL
              AND expires_at > ?
            """,
            (now, token_hash, now),
        )

        if cursor.rowcount != 1:
            return False

        cursor = connection.execute(
            """
            UPDATE users
            SET password_hash = ?
            WHERE user_id = ?
            """,
            (password_hash, token["user_id"]),
        )

        if cursor.rowcount != 1:
            raise RuntimeError(
                "Could not update the account password."
            )

    return True       

def invalidate_password_reset_token(token_hash: str) -> bool:
    """Invalidate an unused password-reset token."""

    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE password_reset_tokens
            SET used_at = ?
            WHERE token_hash = ?
              AND used_at IS NULL
            """,
            (now, token_hash),
        )

    return cursor.rowcount == 1 

initialize_database()