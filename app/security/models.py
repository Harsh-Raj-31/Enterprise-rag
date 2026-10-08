from dataclasses import dataclass, field


@dataclass(frozen=True)
class User:
    """
    Represents an authenticated enterprise user.
    """

    user_id: str
    username: str
    role: str


@dataclass(frozen=True)
class RolePermissions:
    """
    Defines which knowledge sources and actions
    a role is allowed to access.
    """

    role: str

    allowed_sources: frozenset[str] = field(
        default_factory=frozenset
    )

    allowed_actions: frozenset[str] = field(
        default_factory=frozenset
    )

    def can_access(self, source: str) -> bool:
        return source in self.allowed_sources

    def can_perform(self, action: str) -> bool:
        return action in self.allowed_actions
