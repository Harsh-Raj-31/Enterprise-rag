import re


class PromptInjectionGuardrail:
    """
    Detects instruction-like content inside retrieved evidence.

    Retrieved documents must be treated as DATA, not as
    instructions to the LLM.
    """

    INJECTION_PATTERNS = [
        r"\bignore\s+(all\s+)?previous\s+instructions\b",
        r"\bignore\s+(all\s+)?prior\s+instructions\b",
        r"\bdisregard\s+(all\s+)?previous\s+instructions\b",
        r"\bdisregard\s+(all\s+)?prior\s+instructions\b",
        r"\bforget\s+(all\s+)?previous\s+instructions\b",
        r"\boverride\s+(the\s+)?system\s+instructions\b",
        r"\breveal\s+(the\s+)?system\s+prompt\b",
        r"\breveal\s+(confidential|secret|private)\b",
        r"\bshow\s+(me\s+)?(the\s+)?system\s+prompt\b",
        r"\bact\s+as\s+(an?\s+)?(administrator|admin|system)\b",
        r"\byou\s+are\s+now\s+(an?\s+)?administrator\b",
    ]

    def __init__(self):
        self.patterns = [
            re.compile(
                pattern,
                re.IGNORECASE,
            )
            for pattern in self.INJECTION_PATTERNS
        ]

    def contains_injection(
        self,
        text: str,
    ) -> bool:

        if not text or not text.strip():
            return False

        return any(
            pattern.search(text)
            for pattern in self.patterns
        )

    def validate(
        self,
        evidence: list[dict],
    ) -> bool:
        """
        Returns True when the evidence does not contain
        detected prompt-injection instructions.
        """

        if not evidence:
            return True

        for item in evidence:

            text = item.get("text", "")

            if self.contains_injection(text):
                return False

        return True