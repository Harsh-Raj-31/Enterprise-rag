from app.security.document_access import (
    add_access_metadata,
    user_can_access_document,
)
from app.security.models import User


def test_document_access():

    metadata = {
        "source": "salary_database",
        "type": "database",
    }

    secured_metadata = add_access_metadata(
        metadata,
        ["HR", "Admin"],
    )

    assert secured_metadata["allowed_roles"] == [
        "admin",
        "hr",
    ]

    employee = User(
        user_id="EMP101",
        username="aarav",
        role="employee",
    )

    hr_user = User(
        user_id="HR201",
        username="priya",
        role="hr",
    )

    admin_user = User(
        user_id="ADM001",
        username="admin",
        role="admin",
    )

    assert not user_can_access_document(
        employee,
        secured_metadata,
    )

    assert user_can_access_document(
        hr_user,
        secured_metadata,
    )

    assert user_can_access_document(
        admin_user,
        secured_metadata,
    )

    print("Employee access: DENIED")
    print("HR access: ALLOWED")
    print("Admin access: ALLOWED")
    print("\nDocument access test passed.")


if __name__ == "__main__":
    test_document_access()