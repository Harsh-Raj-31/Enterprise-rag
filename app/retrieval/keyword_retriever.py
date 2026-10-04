import re


class KeywordRetriever:
    """
    BM25-based keyword retriever for document chunks.
    """

    def __init__(self, chunks: list[dict]):
        if not chunks:
            raise ValueError(
                "Chunks cannot be empty."
            )

        self.chunks = chunks

        # Tokenize every chunk
        tokenized_documents = [
            self._tokenize(chunk["text"])
            for chunk in chunks
        ]

        from rank_bm25 import BM25Okapi

        self.bm25 = BM25Okapi(
            tokenized_documents
        )

    def _tokenize(self, text: str) -> list[str]:
        """
        Convert text into lowercase word tokens.
        """
        return re.findall(
            r"\b\w+\b",
            text.lower()
        )

    def search(
        self,
        query: str,
        top_k: int = 3,
        allowed_roles: list[str] | None = None
    ) -> list[dict]:
        """
        Retrieve the most relevant chunks using BM25.

        If allowed_roles is provided, only chunks that
        are accessible to at least one of those roles are
        considered for retrieval.
        """

        if not query.strip():
            raise ValueError(
                "Query cannot be empty."
            )

        # ---------------------------------------------
        # Filter chunks by role BEFORE BM25 ranking
        # ---------------------------------------------

        candidate_indices = []

        if allowed_roles:
            normalized_roles = {
                role.strip().lower()
                for role in allowed_roles
                if role.strip()
            }

            if not normalized_roles:
                raise ValueError(
                    "allowed_roles must contain "
                    "at least one valid role."
                )

            for index, chunk in enumerate(
                self.chunks
            ):
                metadata = chunk.get(
                    "metadata",
                    {}
                )

                chunk_roles = {
                    role.lower()
                    for role in metadata.get(
                        "allowed_roles",
                        []
                    )
                }

                if normalized_roles & chunk_roles:
                    candidate_indices.append(index)

        else:
            candidate_indices = list(
                range(len(self.chunks))
            )

        if not candidate_indices:
            return []

        # ---------------------------------------------
        # BM25 scoring
        # ---------------------------------------------

        query_tokens = self._tokenize(query)

        scores = self.bm25.get_scores(
            query_tokens
        )

        ranked_indices = sorted(
            candidate_indices,
            key=lambda index: scores[index],
            reverse=True
        )

        results = []

        for index in ranked_indices[:top_k]:

            results.append(
                {
                    "text": self.chunks[index]["text"],
                    "metadata": self.chunks[index]["metadata"],
                    "score": float(scores[index])
                }
            )

        return results