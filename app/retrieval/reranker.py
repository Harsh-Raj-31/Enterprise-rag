from sentence_transformers import CrossEncoder


class Reranker:
    """
    Cross-encoder based reranker.

    Takes a query and candidate document chunks,
    then assigns a relevance score to each candidate.
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    ):
        self.model_name = model_name
        self.model = CrossEncoder(model_name)

    def rerank(
        self,
        query: str,
        candidates: list[dict],
        top_k: int = 3
    ) -> list[dict]:
        """
        Rerank candidate chunks according to
        query-document relevance.
        """

        if not query.strip():
            raise ValueError(
                "Query cannot be empty."
            )

        if not candidates:
            return []

        pairs = [
            (
                query,
                candidate["text"]
            )
            for candidate in candidates
        ]

        scores = self.model.predict(
            pairs
        )

        reranked = []

        for candidate, score in zip(
            candidates,
            scores
        ):
            result = candidate.copy()

            result["rerank_score"] = float(
                score
            )

            reranked.append(result)

        reranked.sort(
            key=lambda result: result["rerank_score"],
            reverse=True
        )

        return reranked[:top_k]