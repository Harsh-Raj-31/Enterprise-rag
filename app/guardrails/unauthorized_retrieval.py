class UnauthorizedRetrievalGuardrail:
    """
    Defense-in-depth guardrail that verifies retrieved
    evidence is authorized for the current user's role.
    """

    def validate(
        self,
        evidence: list[dict],
        user_role: str | None,
    ) -> bool:

        if not evidence:
            return True

        if not user_role:
            # If evidence contains access metadata,
            # authentication/authorization context is required.
            for item in evidence:

                metadata = item.get(
                    "metadata",
                    {},
                )

                if "allowed_roles" in metadata:
                    return False

            return True

        normalized_user_role = user_role.lower()

        for item in evidence:

            metadata = item.get(
                "metadata",
                {},
            )

            allowed_roles = metadata.get(
                "allowed_roles"
            )

            # Evidence without document-level access metadata
            # is handled by the existing source-specific
            # authorization controls.
            if allowed_roles is None:
                continue

            normalized_roles = {
                role.lower()
                for role in allowed_roles
            }

            if normalized_user_role not in normalized_roles:
                return False

        return True