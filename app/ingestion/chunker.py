import re
from typing import List


class TextChunker:
    """
    Sentence-aware text chunker for RAG documents.
    """

    def __init__(
        self,
        chunk_size: int = 120,
        chunk_overlap: int = 20,
        allowed_roles: list[str] | None = None,
    ):
        if chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap must be smaller than chunk_size."
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.allowed_roles = allowed_roles

    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences while preserving sentence content.
        """

        sentences = re.split(
            r"(?<=[.!?])\s+",
            text.strip()
        )

        return [
            sentence.strip()
            for sentence in sentences
            if sentence.strip()
        ]

    def _create_chunks(
        self,
        sentences: List[str]
    ) -> List[str]:
        """
        Group sentences into chunks without splitting
        sentences unnecessarily.
        """

        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:

            sentence_size = len(sentence.split())

            # If adding this sentence exceeds the target,
            # save the current chunk first.
            if (
                current_chunk
                and current_size + sentence_size > self.chunk_size
            ):
                chunks.append(
                    " ".join(current_chunk)
                )

                # Keep the last few sentences as overlap.
                overlap_sentences = []
                overlap_size = 0

                for previous_sentence in reversed(current_chunk):

                    previous_size = len(
                        previous_sentence.split()
                    )

                    if overlap_size + previous_size > self.chunk_overlap:
                        break

                    overlap_sentences.insert(
                        0,
                        previous_sentence
                    )

                    overlap_size += previous_size

                current_chunk = overlap_sentences
                current_size = overlap_size

            current_chunk.append(sentence)
            current_size += sentence_size

        if current_chunk:
            chunks.append(
                " ".join(current_chunk)
            )

        return chunks

    def chunk_documents(
        self,
        documents: List[dict]
    ) -> List[dict]:
        """
        Convert page-level documents into sentence-aware
        chunks while preserving metadata.
        """

        chunks = []

        for document in documents:

            text = document["text"]
            metadata = document["metadata"]

            sentences = self._split_sentences(text)

            page_chunks = self._create_chunks(
                sentences
            )

            for index, chunk_text in enumerate(
                page_chunks,
                start=1
            ):

                chunk_metadata = metadata.copy()

                if "page" in metadata:
                    chunk_id = (
                        f"{metadata['source']}"
                        f"_p{metadata['page']}"
                        f"_c{index}"
                    )

                elif "row" in metadata:

                    if "sheet" in metadata:
                        chunk_id = (
                            f"{metadata['source']}"
                            f"_{metadata['sheet']}"
                            f"_r{metadata['row']}"
                            f"_c{index}"
                        )
                    else:
                        chunk_id = (
                            f"{metadata['source']}"
                            f"_r{metadata['row']}"
                            f"_c{index}"
                        )

                else:
                    chunk_id = (
                        f"{metadata['source']}"
                        f"_c{index}"
                    )

                chunk_metadata.update({
                    "chunk_id": chunk_id,
                    "chunk_index": index,
                })

                if self.allowed_roles is not None:

                    normalized_roles = {
                        role.strip().lower()
                        for role in self.allowed_roles
                        if role.strip()
                    }

                    if not normalized_roles:
                        raise ValueError(
                            "allowed_roles must contain "
                            "at least one valid role."
                        )

                    # Keep the human-readable role list.
                    chunk_metadata["allowed_roles"] = sorted(
                        normalized_roles
                    )

                    # Explicitly set every supported role.
                    # This prevents stale metadata from previous
                    # ingestion operations from granting access.
                    supported_roles = {
                        "employee",
                        "manager",
                        "hr",
                        "admin",
                    }

                    for role in supported_roles:
                        chunk_metadata[f"access_{role}"] = (
                            role in normalized_roles
                        )

                chunks.append(
                    {
                        "text": chunk_text,
                        "metadata": chunk_metadata,
                    }
                )

        return chunks
