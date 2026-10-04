from app.security.access_control import AccessController
from app.security.models import User


def test_access_control():

    controller = AccessController()

    employee = User(
        user_id="EMP101",
        username="aarav",
        role="employee",
    )

    # Employee should be allowed to access HR policies.
    controller.require_access(
        employee,
        "hr_policy",
    )

    print("HR policy access granted")

    # Employee should NOT be allowed to access
    # the salary database.
    try:
        controller.require_access(
            employee,
            "salary_database",
        )

        raise AssertionError(
            "ERROR: unauthorized access was granted"
        )

    except PermissionError as exc:

        print(
            "Salary database access blocked:",
            exc,
        )


if __name__ == "__main__":
    test_access_control()
    print("\nAccess control test passed.")