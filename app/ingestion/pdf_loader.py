import pymupdf
from pathlib import Path


class PDFLoader:
    """Load and extract text from PDF documents."""

    def load(self, file_path: str) -> list[dict]:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"PDF file not found: {file_path}"
            )

        if path.suffix.lower() != ".pdf":
            raise ValueError(
                "The provided file must be a PDF."
            )

        documents = []

        pdf = pymupdf.open(file_path)

        try:
            for page_number, page in enumerate(pdf, start=1):
                text = page.get_text("text").strip()

                if not text:
                    continue

                documents.append(
                    {
                        "text": text,
                        "metadata": {
                            "source": path.name,
                            "page": page_number,
                            "file_path": str(path),
                        },
                    }
                )
        finally:
            pdf.close()

        return documents