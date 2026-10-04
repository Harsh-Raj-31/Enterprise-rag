from app.agents.graph import build_graph
from app.ingestion.pdf_loader import PDFLoader
from app.ingestion.chunker import TextChunker


PDF_PATH = "data/raw/employee_policy.pdf"


def build_chunks():
    loader = PDFLoader()
    documents = loader.load(PDF_PATH)

    chunker = TextChunker()
    return chunker.chunk_documents(documents)


def test_pdf_graph():
    chunks = build_chunks()

    graph = build_graph(chunks)

    result = graph.invoke(
        {
            "query": "How many annual leave days do employees receive?",
            "route": "pdf",
        }
    )

    assert result["route"] == "pdf"
    assert result["answer"]
    assert result["sources"]

    print("\nLANGGRAPH PDF TEST")
    print("=" * 60)

    print("Route:")
    print(result["route"])

    print("\nAnswer:")
    print(result["answer"])

    print("\nSources:")

    for source in result["sources"]:
        print(source)


if __name__ == "__main__":
    test_pdf_graph()

    print("\nLangGraph PDF workflow test passed.")