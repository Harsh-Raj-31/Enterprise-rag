from app.security.models import User
from app.security.permissions import get_role_permissions


class AccessController:
    """
    Enforces role-based access control before
    knowledge-source retrieval.
    """

    def can_access(
        self,
        user: User,
        source: str,
    ) -> bool:
        """
        Check whether the user's role can access
        the requested knowledge source.
        """

        permissions = get_role_permissions(user.role)

        return permissions.can_access(source)

    def require_access(
        self,
        user: User,
        source: str,
    ) -> None:
        """
        Enforce access to a knowledge source.

        Raises PermissionError when access is denied.
        """

        if not self.can_access(user, source):
            raise PermissionError(
                f"Access denied: role '{user.role}' "
                f"cannot access '{source}'."
            )