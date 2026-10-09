import pytest

import app.security.user_repository as repository
from app.security.users import authenticate_user, register_user


@pytest.fixture
def isolated_database(tmp_path, monkeypatch):
    """Give each test its own SQLite database."""

    test_db = tmp_path / "registration_test.sqlite3"

    monkeypatch.setattr(repository, "DB_PATH", test_db)
    repository.initialize_database()

    yield repository


def test_registration_creates_employee(isolated_database):
    user = register_user(
        full_name="Test Employee",
        username="newemployee",
        email="newemployee@example.com",
        password="StrongTestPassword123!",
    )

    assert user["username"] == "newemployee"
    assert user["email"] == "newemployee@example.com"
    assert user["role"] == "employee"


def test_registered_user_can_login(isolated_database):
    register_user(
        full_name="Test Employee",
        username="loginemployee",
        email="loginemployee@example.com",
        password="StrongTestPassword123!",
    )

    user = authenticate_user(
        "loginemployee",
        "StrongTestPassword123!",
    )

    assert user is not None
    assert user.username == "loginemployee"
    assert user.role == "employee"


def test_registration_rejects_duplicate_username(isolated_database):
    register_user(
        full_name="First Employee",
        username="duplicateuser",
        email="first@example.com",
        password="StrongTestPassword123!",
    )

    with pytest.raises(ValueError):
        register_user(
            full_name="Second Employee",
            username="duplicateuser",
            email="second@example.com",
            password="AnotherStrongPassword123!",
        )


def test_registration_rejects_duplicate_email(isolated_database):
    register_user(
        full_name="First Employee",
        username="firstuser",
        email="shared@example.com",
        password="StrongTestPassword123!",
    )

    with pytest.raises(ValueError):
        register_user(
            full_name="Second Employee",
            username="seconduser",
            email="shared@example.com",
            password="AnotherStrongPassword123!",
        )


def test_registration_cannot_use_demo_username(isolated_database):
    with pytest.raises(ValueError):
        register_user(
            full_name="Fake Administrator",
            username="admin",
            email="fakeadmin@example.com",
            password="StrongTestPassword123!",
        )