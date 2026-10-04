from pathlib import Path

from app.agents.pdf_agent import PDFAgent
from app.ingestion.pdf_loader import PDFLoader
from app.ingestion.chunker import TextChunker


PDF_PATH = "data/raw/employee_policy.pdf"


def build_chunks():
    loader = PDFLoader()
    documents = loader.load(PDF_PATH)

    chunker = TextChunker()
    chunks = chunker.chunk_documents(documents)

    return chunks


def test_pdf_agent():
    chunks = build_chunks()

    agent = PDFAgent(chunks)

    state = {
        "query": "How many annual leave days do employees receive?",
        "route": "pdf",
    }

    result = agent.run(state)

    assert result["answer"]
    assert result["sources"]

    print("\nPDF AGENT TEST")
    print("=" * 60)
    print("Query:")
    print(result["query"])
    print("\nAnswer:")
    print(result["answer"])
    print("\nSources:")

    for source in result["sources"]:
        print(source)


if __name__ == "__main__":
    test_pdf_agent()
    print("\nPDF Agent test passed.")