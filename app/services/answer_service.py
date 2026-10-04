from app.services.llm_service import LLMService
from app.guardrails.grounding import GroundingGuardrail
from app.guardrails.prompt_injection import PromptInjectionGuardrail
from app.guardrails.unauthorized_retrieval import (
    UnauthorizedRetrievalGuardrail,
)


class AnswerService:
    """
    Common answer-generation layer used by
    PDF, Web, and Database agents.
    """

    def __init__(self):
        self.llm_service = LLMService()
        self.grounding_guardrail = GroundingGuardrail()
        self.prompt_injection_guardrail = PromptInjectionGuardrail()
        self.unauthorized_retrieval_guardrail = (
            UnauthorizedRetrievalGuardrail()
        )

    def generate(
        self,
        query: str,
        evidence: list[dict],
        user_role: str | None = None,
    ) -> str:

        if not query.strip():
            raise ValueError("Query cannot be empty.")

        if not evidence:
            return (
                "I could not find relevant information "
                "in the available knowledge sources."
            )

        context = []

        for item in evidence:
            metadata = {
                "source": item.get(
                    "source",
                    item.get("url", "Unknown source"),
                ),
                "page": item.get("page", "N/A"),
            }

            # Preserve authorization metadata for
            # defense-in-depth checks.
            if "allowed_roles" in item:
                metadata["allowed_roles"] = item["allowed_roles"]

            context.append({
                "text": self._format_evidence(item),
                "metadata": metadata,
            })

        # Unauthorized retrieval defense-in-depth.
        if not self.unauthorized_retrieval_guardrail.validate(
            evidence=context,
            user_role=user_role,
        ):
            return (
                "I could not process the retrieved information "
                "because you are not authorized to access "
                "one or more of the retrieved resources."
            )

        # Prompt injection protection.
        if not self.prompt_injection_guardrail.validate(
            context
        ):
            return (
                "I could not process the retrieved information "
                "because it contains potentially unsafe instructions."
            )

        # Generate answer using the LLM.
        answer = self.llm_service.generate_answer(
            query=query,
            context=context,
        )

        # Grounding protection.
        grounding_valid = self.grounding_guardrail.validate(
            answer=answer,
            evidence=context,
        )

        if not grounding_valid:
            return (
                "I could not provide a reliable answer "
                "based on the available knowledge evidence."
            )

        # Return the validated grounded answer.
        return answer

    def _format_evidence(
        self,
        item: dict,
    ) -> str:
        """
        Convert agent-specific evidence into
        readable context for the LLM.
        """

        if "text" in item:
            return item["text"]

        if "employee_id" in item:
            return (
                f"Employee ID: {item['employee_id']}\n"
                f"Name: {item.get('name', 'Unknown')}\n"
                f"Department: {item.get('department', 'Unknown')}\n"
                f"Role: {item.get('role', 'Unknown')}"
            )

        return str(item)