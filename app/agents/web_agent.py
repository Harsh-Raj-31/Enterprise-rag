import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

from app.agents.state import AgentState
from app.agents.result import AgentResult
from app.services.answer_service import AnswerService
from app.retrieval.retriever import Retriever
from app.security.network_security import validate_hostname


class WebAgent:
    """
    Web Agent supporting two retrieval modes:

    1. Live-web mode:
       Fetch a webpage when a URL is explicitly supplied.

    2. Ingested-source mode:
       Retrieve previously ingested website chunks
       from ChromaDB.
    """

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.answer_service = AnswerService()
        self.retriever = Retriever()

    def validate_url(self, url: str) -> None:
        parsed = urlparse(url)

        if parsed.scheme not in {"http", "https"}:
            raise ValueError(
                "Only HTTP and HTTPS URLs are allowed."
            )

        if not parsed.hostname:
            raise ValueError(
                "Invalid URL: hostname is required."
            )

        validate_hostname(parsed.hostname)

    def fetch_page(self, url: str) -> str:
        self.validate_url(url)

        current_url = url
        max_redirects = 5

        for _ in range(max_redirects + 1):
            response = requests.get(
                current_url,
                timeout=self.timeout,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 "
                        "(Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 "
                        "Chrome/120 Safari/537.36"
                    )
                },
                allow_redirects=False,
            )

            if (
                response.is_redirect
                or response.is_permanent_redirect
            ):
                location = response.headers.get("Location")

                if not location:
                    raise ValueError(
                        "Redirect response does not "
                        "contain a destination."
                    )

                next_url = urljoin(
                    current_url,
                    location,
                )

                # Validate every redirect destination
                # before making another request.
                self.validate_url(next_url)

                current_url = next_url
                continue

            response.raise_for_status()
            break

        else:
            raise ValueError(
                "Too many redirects."
            )

        content_type = response.headers.get(
            "Content-Type",
            "",
        ).lower()

        if "text/html" not in content_type:
            raise ValueError(
                "The supplied URL must return an HTML page."
            )

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        for element in soup(
            [
                "script",
                "style",
                "noscript",
                "header",
                "footer",
                "nav",
                "aside",
            ]
        ):
            element.decompose()

        text = soup.get_text(
            separator=" ",
            strip=True,
        )

        if not text:
            raise ValueError(
                "No readable text found on the webpage."
            )

        return text

    def retrieve_ingested_websites(
        self,
        query: str,
        user_role: str | None,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Retrieve accessible website chunks from ChromaDB.
        """

        if not user_role:
            raise PermissionError(
                "An authenticated user role is required "
                "to search ingested websites."
            )

        results = self.retriever.retrieve(
            query=query,
            top_k=top_k,
            where={
                "document_type": "website",
            },
            allowed_roles=[user_role],
        )

        evidence = []

        for result in results:
            metadata = result.get("metadata", {})

            item = {
                "text": result["text"],
                "source": metadata.get(
                    "source",
                    metadata.get("url", "Unknown source"),
                ),
                "url": metadata.get("url"),
                "chunk_id": metadata.get(
                    "chunk_id",
                    "unknown",
                ),
                "title": metadata.get("title"),
                "document_type": "website",
            }

            # Preserve document-level authorization metadata
            # for the answer-generation guardrail.
            if "allowed_roles" in metadata:
                item["allowed_roles"] = metadata[
                    "allowed_roles"
                ]

            evidence.append(item)

        return evidence


    def run(self, state):
        query = state["query"]
        url = state.get("url")
        user_role = state.get("user_role")

        if url:
            # Live website mode
            text = self.fetch_page(url)
            evidence = [
                {
                    "source": url,
                    "url": url,
                    "text": text[:5000],
                    "document_type": "website",
                }
            ]
        else:
            # Retrieve previously ingested website chunks
            evidence = self.retrieve_ingested_websites(
                query=query,
                user_role=user_role,
            )

        answer = self.answer_service.generate(
            query=query,
            evidence=evidence,
            user_role=user_role,
        )

        sources = []
        for item in evidence:
            source = {
                "url": item.get("url"),
                "source": item.get("source", item.get("url")),
            }

            if item.get("chunk_id"):
                source["chunk_id"] = item["chunk_id"]

            if item.get("title"):
                source["title"] = item["title"]

            sources.append(source)

        return {
            **state,
            "answer": answer,
            "evidence": evidence,
            "sources": sources,
        }
