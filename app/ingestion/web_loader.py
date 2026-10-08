from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from app.security.network_security import validate_hostname


class WebLoader:
    """
    Load and clean text content from a website.
    """

    def __init__(self, timeout: int = 10, max_redirects: int = 5):
        self.timeout = timeout
        self.max_redirects = max_redirects

    def validate_url(self, url: str) -> None:
        parsed = urlparse(url)

        if parsed.scheme not in {"http", "https"}:
            raise ValueError(
                "Only HTTP and HTTPS URLs are allowed."
            )

        if not parsed.netloc:
            raise ValueError(
                "Invalid URL: hostname is missing."
            )

        validate_hostname(parsed.hostname)

    def load(self, url: str) -> list[dict]:
        """
        Fetch a website and return it using the same
        document structure as PDFLoader.
        """

        self.validate_url(url)

        current_url = url

        for _ in range(self.max_redirects + 1):
            self.validate_url(current_url)

            response = requests.get(
                current_url,
                timeout=self.timeout,
                headers={
                    "User-Agent": (
                        "Enterprise-RAG/1.0 "
                        "(knowledge ingestion)"
                    )
                },
                allow_redirects=False,
            )

            if response.is_redirect or response.is_permanent_redirect:
                location = response.headers.get("Location")

                if not location:
                    raise ValueError(
                        "Website returned a redirect without "
                        "a destination."
                    )

                from urllib.parse import urljoin

                current_url = urljoin(
                    current_url,
                    location,
                )
                continue

            response.raise_for_status()
            break

        else:
            raise ValueError(
                "Too many redirects while loading website."
            )

        content_type = response.headers.get(
            "Content-Type",
            "",
        ).lower()

        if "text/html" not in content_type:
            raise ValueError(
                "The provided URL does not return an HTML page."
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

        title = (
            soup.title.get_text(strip=True)
            if soup.title
            else ""
        )

        text = soup.get_text(
            separator=" ",
            strip=True,
        )

        if not text:
            raise ValueError(
                "No readable text was found on the website."
            )

        return [
            {
                "text": text,
                "metadata": {
                    "source": current_url,
                    "url": current_url,
                    "title": title,
                    "document_type": "website",
                },
            }
        ]