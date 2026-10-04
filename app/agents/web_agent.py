import requests
from bs4 import BeautifulSoup

from app.agents.state import AgentState
from app.agents.result import AgentResult
from app.services.answer_service import AnswerService
from urllib.parse import urlparse
from app.security.network_security import validate_hostname


class WebAgent:
    """
    Agent responsible for retrieving readable text
    from a web page.
    """

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.answer_service = AnswerService()


    def validate_url(self, url: str) -> None:

        parsed = urlparse(url)

        if parsed.scheme not in {"http", "https"}:
            raise ValueError(
                "Only HTTP and HTTPS URLs are allowed."
            )

        if not parsed.netloc:
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

            if response.is_redirect or response.is_permanent_redirect:
                location = response.headers.get("Location")

                if not location:
                    raise ValueError(
                        "Redirect response does not contain a destination."
                    )

                # Resolve relative redirects such as:
                # /next-page
                # against the current URL.
                from urllib.parse import urljoin

                next_url = urljoin(current_url, location)

                # Validate the redirect destination BEFORE requesting it.
                self.validate_url(next_url)

                current_url = next_url
                continue

            response.raise_for_status()
            break

        else:
            raise ValueError(
                "Too many redirects."
            )

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        for element in soup(
            ["script", "style", "noscript", "header", "footer"]
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


    def run(self, state: AgentState) -> AgentState:

        url = state.get("url")
        user_role = state.get("user_role")

        if not url:
            raise ValueError(
                "Web Agent requires a URL."
            )

        # Retrieve webpage content
        text = self.fetch_page(url)

        # Standardized evidence
        evidence = [
            {
                "url": url,
                "source": url,
                "text": text[:5000],
            }
        ]

        # Generate grounded answer through
        # the common answer-generation layer
        answer = self.answer_service.generate(
            query=state["query"],
            evidence=evidence,
            user_role=user_role,
        )

        agent_result: AgentResult = {
            "source_type": "web",
            "answer": answer,
            "evidence": evidence,
            "sources": [
                {
                    "url": url,
                }
            ],
        }

        return {
            **state,
            "answer": agent_result["answer"],
            "evidence": agent_result["evidence"],
            "sources": agent_result["sources"],
        }