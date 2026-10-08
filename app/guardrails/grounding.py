import re


class GroundingGuardrail:
    """
    Validates whether an answer is sufficiently supported
    by the retrieved evidence.
    """

    def __init__(self, min_overlap: float = 0.15):
        self.min_overlap = min_overlap

    def validate(
        self,
        answer: str,
        evidence: list[dict],
    ) -> bool:

        if not answer or not answer.strip():
            return False

        if not evidence:
            return False

        evidence_text = " ".join(
            item.get("text", "")
            for item in evidence
        )

        # Remove source/page citation metadata before
        # validating the factual content of the answer.
        clean_answer = self._remove_citations(answer)

        answer_words = self._normalize(clean_answer)
        evidence_words = self._normalize(evidence_text)

        if not answer_words:
            return False

        # Check for contradictory numeric values.
        if self._has_numeric_contradiction(
            clean_answer,
            evidence_text,
        ):
            return False

        # Check individual claims in the answer.
        if self._has_unsupported_claim(
            clean_answer,
            evidence_text,
        ):
            return False

        # Overall answer-level overlap check.
        overlap = answer_words.intersection(
            evidence_words
        )

        overlap_ratio = (
            len(overlap) / len(answer_words)
        )

        return overlap_ratio >= self.min_overlap

    def _remove_citations(
        self,
        answer: str,
    ) -> str:
        """
        Remove source/page citation metadata before
        validating factual content.

        Examples:
            (employee_policy.pdf, page 2)
            Source: employee_policy.pdf, page 2.
            See employee_policy.pdf, page 2.
            See employee_policy.pdf, p. 2.
        """

        # Remove parenthesized citations.
        answer = re.sub(
            r"\(\s*[^()]*\.(?:pdf|txt|docx?)"
            r"\s*,\s*(?:page|p\.)\s*\d+\s*\)",
            "",
            answer,
            flags=re.IGNORECASE,
        )

        # Remove "Source: filename.pdf, page N".
        answer = re.sub(
            r"\bsource\s*:\s*"
            r"[^,\n]+?\.(?:pdf|txt|docx?)"
            r"\s*,\s*(?:page|p\.)\s*\d+"
            r"\.?",
            "",
            answer,
            flags=re.IGNORECASE,
        )

        # Remove "See filename.pdf, page N".
        answer = re.sub(
            r"\bsee\s+"
            r"[^,\n]+?\.(?:pdf|txt|docx?)"
            r"\s*,\s*(?:page|p\.)\s*\d+"
            r"\.?",
            "",
            answer,
            flags=re.IGNORECASE,
        )

        # Remove "See filename.pdf, page N".
        answer = re.sub(
            r"\bsee\s+"
            r"[^,\n]+?\.(?:pdf|txt|docx?)"
            r"\s*,\s*(?:page|p\.)\s*\d+"
            r"\.?",
            "",
            answer,
            flags=re.IGNORECASE,
        )

        # Remove "Source: filename.csv/xlsx/xls".
        answer = re.sub(
            r"\bsource\s*:\s*"
            r"[^,\n]+?\.(?:csv|xlsx?|xls)"
            r"\.?",
            "",
            answer,
            flags=re.IGNORECASE,
        )

        return answer

    def _has_numeric_contradiction(
        self,
        answer: str,
        evidence: str,
    ) -> bool:

        answer_numbers = set(
            re.findall(
                r"\b\d+(?:\.\d+)?\b",
                answer,
            )
        )

        evidence_numbers = set(
            re.findall(
                r"\b\d+(?:\.\d+)?\b",
                evidence,
            )
        )

        if not answer_numbers:
            return False

        return not answer_numbers.issubset(
            evidence_numbers
        )

    def _has_unsupported_claim(
        self,
        answer: str,
        evidence_text: str,
    ) -> bool:

        # Split into sentences.
        sentences = [
            sentence.strip()
            for sentence in re.split(
                r"[.!?]+",
                answer,
            )
            if sentence.strip()
        ]

        evidence_words = self._normalize(
            evidence_text
        )

        for sentence in sentences:

            # Split compound claims connected by "and".
            claims = re.split(
                r"\s+\band\b\s+",
                sentence,
                flags=re.IGNORECASE,
            )

            for claim in claims:

                claim_words = self._normalize(
                    claim
                )

                if not claim_words:
                    continue

                overlap = claim_words.intersection(
                    evidence_words
                )

                overlap_ratio = (
                    len(overlap) / len(claim_words)
                )

                if overlap_ratio < self.min_overlap:
                    return True

        return False

    def _normalize(
        self,
        text: str,
    ) -> set[str]:

        # Normalize structured text such as:
        # "name: Ananya Singh | role:AI Engineer"
        # into individual searchable words.
        words = re.findall(
            r"[a-zA-Z0-9]+(?:['-][a-zA-Z0-9]+)*",
            text.lower(),
        )

        # Ignore common stop words that do not carry
        # factual meaning for grounding validation.
        stop_words = {
            "the",
            "is",
            "a",
            "an",
            "and",
            "or",
            "of",
            "to",
            "in",
            "on",
            "for",
            "with",
            "who",
            "what",
            "which",
            "source",
        }

        return {
            word
            for word in words
            if len(word) > 2
            and word not in stop_words
        }
