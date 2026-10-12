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
        """
        Validate the answer against the supplied evidence.

        Checks:
        1. Answer and evidence are not empty.
        2. Numeric values are supported by the evidence.
        3. Individual claims have sufficient evidence overlap.
        4. The overall answer has sufficient evidence overlap.
        """

        if not answer or not answer.strip():
            return False

        if not evidence:
            return False

        evidence_text = " ".join(
            item.get("text", "")
            for item in evidence
        )

        # Remove citations before validating factual content.
        clean_answer = self._remove_citations(answer)

        answer_words = self._normalize(clean_answer)
        evidence_words = self._normalize(evidence_text)

        if not answer_words:
            return False

        # Check for unsupported numeric values.
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

        # Check overall answer-level evidence overlap.
        overlap = answer_words.intersection(evidence_words)

        overlap_ratio = len(overlap) / len(answer_words)

        return overlap_ratio >= self.min_overlap

    def _remove_citations(
        self,
        answer: str,
    ) -> str:
        """
        Remove citation metadata before validating factual content.

        Supported examples:
            [Evidence 1]
            【Evidence 1】
            (employee_policy.pdf, page 2)
            Source: employee_policy.pdf, page 2.
            See employee_policy.pdf, page 2.
            See employee_policy.pdf, p. 2.
            Source: employees.csv
        """

        # Remove generated evidence-reference markers.
        # Supports both ASCII and Unicode brackets.
        # Remove evidence-reference markers:
        # [Evidence 1]
        # 【Evidence 1】
        # 【1†L1-L4】
        # 【2†L13-L16】
        answer = re.sub(
            r"(?:"
            r"[\[【]\s*Evidence\s+\d+\s*[\]】]"
            r"|"
            r"【\s*\d+\s*†\s*L\d+(?:\s*-\s*L?\d+)?\s*】"
            r")",
            "",
            answer,
            flags=re.IGNORECASE,
)
        # Remove parenthesized PDF, TXT, DOC, and DOCX citations.
        # Example: (employee_policy.pdf, page 2)
        answer = re.sub(
            r"\(\s*[^()\n]+\.(?:pdf|txt|docx?)"
            r"\s*,\s*(?:page|p\.?)\s*\d+\s*\)",
            "",
            answer,
            flags=re.IGNORECASE,
        )

        # Remove source citations for document files.
        # Example: Source: employee_policy.pdf, page 2.
        answer = re.sub(
            r"\bsource\s*:\s*[^,\n]+?\.(?:pdf|txt|docx?)"
            r"\s*,\s*(?:page|p\.?)\s*\d+\.?",
            "",
            answer,
            flags=re.IGNORECASE,
        )

        # Remove references such as:
        # See employee_policy.pdf, page 2.
        # See employee_policy.pdf, p. 2.
        answer = re.sub(
            r"\bsee\s+[^,\n]+?\.(?:pdf|txt|docx?)"
            r"\s*,\s*(?:page|p\.?)\s*\d+\.?",
            "",
            answer,
            flags=re.IGNORECASE,
        )

        # Remove CSV and Excel source citations.
        # Examples: Source: employees.csv
        #           Source: report.xlsx
        answer = re.sub(
            r"\bsource\s*:\s*[^,\n]+?\.(?:csv|xlsx?|xls)\b\.?",
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
        """
        Return True if the answer contains numeric values
        that do not appear in the evidence.
        """

        number_pattern = r"\b\d+(?:\.\d+)?\b"

        answer_numbers = set(
            re.findall(number_pattern, answer)
        )

        evidence_numbers = set(
            re.findall(number_pattern, evidence)
        )

        if not answer_numbers:
            return False

        return not answer_numbers.issubset(evidence_numbers)

    def _has_unsupported_claim(
        self,
        answer: str,
        evidence_text: str,
    ) -> bool:
        """
        Check whether individual answer claims have sufficient
        word overlap with the evidence.
        """

        # Split the answer into sentences.
        sentences = [
            sentence.strip()
            for sentence in re.split(
                r"[.!?]+",
                answer,
            )
            if sentence.strip()
        ]

        evidence_words = self._normalize(evidence_text)

        for sentence in sentences:

            # Split compound claims connected by "and".
            claims = re.split(
                r"\s+\band\b\s+",
                sentence,
                flags=re.IGNORECASE,
            )

            for claim in claims:
                claim_words = self._normalize(claim)

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
        """
        Normalize text into searchable words and remove
        common stop words.
        """

        words = re.findall(
            r"[a-zA-Z0-9]+(?:['-][a-zA-Z0-9]+)*",
            text.lower(),
        )

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