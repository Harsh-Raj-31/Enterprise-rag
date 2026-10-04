from app.retrieval.retriever import Retriever
from app.retrieval.keyword_retriever import KeywordRetriever
from app.retrieval.reranker import Reranker


class HybridRetriever:
    """
    Combines semantic vector retrieval and BM25
    keyword retrieval.
    """

    def __init__(
        self,
        chunks: list[dict],
        vector_retriever: Retriever | None = None
    ):
        self.chunks = chunks

        self.keyword_retriever = KeywordRetriever(
            chunks
        )

        self.vector_retriever = (
            vector_retriever
            or Retriever()
        )
        self.reranker = Reranker()

    def _normalize_scores(
        self,
        scores: list[float],
        higher_is_better: bool = True
    ) -> list[float]:
        """
        Normalize scores to the range 0-1.
        """

        if not scores:
            return []

        minimum = min(scores)
        maximum = max(scores)

        # All scores are identical
        if maximum == minimum:
            return [1.0] * len(scores)

        normalized = []

        for score in scores:

            if higher_is_better:
                value = (
                    (score - minimum)
                    / (maximum - minimum)
                )

            else:
                value = (
                    (maximum - score)
                    / (maximum - minimum)
                )

            normalized.append(value)

        return normalized

    def search(
        self,
        query: str,
        top_k: int = 3,
        vector_weight: float = 0.5,
        keyword_weight: float = 0.5,
        allowed_roles: list[str] | None = None
    ) -> list[dict]:
        """
        Perform hybrid retrieval using vector search
        and BM25 keyword search.
        """

        if not query.strip():
            raise ValueError(
                "Query cannot be empty."
            )

        if vector_weight + keyword_weight <= 0:
            raise ValueError(
                "At least one retrieval weight must be greater than zero."
            )

        # Retrieve more candidates than we finally return.
        candidate_k = max(top_k, 5)

        vector_results = (
            self.vector_retriever.retrieve(
                query,
                top_k=candidate_k,
                allowed_roles=allowed_roles
            )
        )

        keyword_results = (
            self.keyword_retriever.search(
                query,
                top_k=candidate_k,
                allowed_roles=allowed_roles
            )
        )

        # -------------------------------------------------
        # Vector scores
        # Chroma distance: LOWER = better
        # -------------------------------------------------

        vector_distances = [
            result["distance"]
            for result in vector_results
        ]

        vector_scores = self._normalize_scores(
            vector_distances,
            higher_is_better=False
        )

        vector_map = {}

        for result, score in zip(
            vector_results,
            vector_scores
        ):
            chunk_id = result["metadata"]["chunk_id"]

            vector_map[chunk_id] = {
                "score": score,
                "result": result
            }

        # -------------------------------------------------
        # BM25 scores
        # BM25: HIGHER = better
        # -------------------------------------------------

        keyword_scores = [
            result["score"]
            for result in keyword_results
        ]

        keyword_scores = self._normalize_scores(
            keyword_scores,
            higher_is_better=True
        )

        keyword_map = {}

        for result, score in zip(
            keyword_results,
            keyword_scores
        ):
            chunk_id = result["metadata"]["chunk_id"]

            keyword_map[chunk_id] = {
                "score": score,
                "result": result
            }

        # -------------------------------------------------
        # Combine candidates
        # -------------------------------------------------

        all_chunk_ids = set(
            vector_map.keys()
        ) | set(
            keyword_map.keys()
        )

        hybrid_results = []

        for chunk_id in all_chunk_ids:

            vector_score = (
                vector_map
                .get(chunk_id, {})
                .get("score", 0.0)
            )

            keyword_score = (
                keyword_map
                .get(chunk_id, {})
                .get("score", 0.0)
            )

            result = (
                vector_map.get(
                    chunk_id,
                    keyword_map.get(chunk_id)
                )["result"]
            )

            hybrid_score = (
                vector_weight * vector_score
                + keyword_weight * keyword_score
            )

            hybrid_results.append(
                {
                    "text": result["text"],
                    "metadata": result["metadata"],
                    "vector_score": vector_score,
                    "keyword_score": keyword_score,
                    "hybrid_score": hybrid_score
                }
            )

        # Highest hybrid score first
        hybrid_results.sort(
            key=lambda result: result["hybrid_score"],
            reverse=True
        )
        reranked_results = self.reranker.rerank(
            query=query,
            candidates=hybrid_results,
            top_k=top_k
        )

        return reranked_results