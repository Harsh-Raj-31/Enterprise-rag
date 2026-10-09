import sqlite3

import pytest

from app.security.password import hash_password, verify_password
from app.security.user_repository import (
    create_user,
    get_user_by_email,
    get_user_by_username,
    update_password_hash,
)


@pytest.fixture
def isolated_database(tmp_path, monkeypatch):
    """Use a temporary database so tests never modify real accounts."""

    import app.security.user_repository as repository

    test_db = tmp_path / "test_users.sqlite3"

    monkeypatch.setattr(repository, "DB_PATH", test_db)
    repository.initialize_database()

    yield repository


def test_create_user_assigns_employee_role(isolated_database):
    password_hash = hash_password("StrongTestPassword123!")

    user = isolated_database.create_user(
        full_name="Test Employee",
        username="test_employee",
        email="employee@example.com",
        password_hash=password_hash,
    )

    assert user is not None
    assert user["username"] == "test_employee"
    assert user["email"] == "employee@example.com"
    assert user["role"] == "employee"
    assert verify_password(
        "StrongTestPassword123!",
        user["password_hash"],
    )


def test_lookup_user_by_username(isolated_database):
    isolated_database.create_user(
        full_name="Test Employee",
        username="employee_one",
        email="employee1@example.com",
        password_hash=hash_password("TestPassword123!"),
    )

    user = isolated_database.get_user_by_username("employee_one")

    assert user is not None
    assert user["username"] == "employee_one"


def test_lookup_user_by_email(isolated_database):
    isolated_database.create_user(
        full_name="Test Employee",
        username="employee_two",
        email="employee2@example.com",
        password_hash=hash_password("TestPassword123!"),
    )

    user = isolated_database.get_user_by_email("employee2@example.com")

    assert user is not None
    assert user["username"] == "employee_two"


def test_duplicate_username_is_rejected(isolated_database):
    password_hash = hash_password("TestPassword123!")

    isolated_database.create_user(
        full_name="First Employee",
        username="same_username",
        email="first@example.com",
        password_hash=password_hash,
    )

    with pytest.raises(sqlite3.IntegrityError):
        isolated_database.create_user(
            full_name="Second Employee",
            username="same_username",
            email="second@example.com",
            password_hash=password_hash,
        )


def test_duplicate_email_is_rejected(isolated_database):
    password_hash = hash_password("TestPassword123!")

    isolated_database.create_user(
        full_name="First Employee",
        username="first_user",
        email="shared@example.com",
        password_hash=password_hash,
    )

    with pytest.raises(sqlite3.IntegrityError):
        isolated_database.create_user(
            full_name="Second Employee",
            username="second_user",
            email="shared@example.com",
            password_hash=password_hash,
        )


def test_username_uniqueness_is_case_insensitive(isolated_database):
    isolated_database.create_user(
        full_name="First Employee",
        username="CaseUser",
        email="case1@example.com",
        password_hash=hash_password("TestPassword123!"),
    )

    with pytest.raises(sqlite3.IntegrityError):
        isolated_database.create_user(
            full_name="Second Employee",
            username="caseuser",
            email="case2@example.com",
            password_hash=hash_password("TestPassword123!"),
        )


def test_password_hash_can_be_updated(isolated_database):
    user = isolated_database.create_user(
        full_name="Password Test",
        username="password_user",
        email="password@example.com",
        password_hash=hash_password("OldPassword123!"),
    )

    updated = isolated_database.update_password_hash(
        user["user_id"],
        hash_password("NewPassword123!"),
    )

    stored_user = isolated_database.get_user_by_username("password_user")

    assert updated is True
    assert verify_password(
        "NewPassword123!",
        stored_user["password_hash"],
    )
    assert not verify_password(
        "OldPassword123!",
        stored_user["password_hash"],
    )