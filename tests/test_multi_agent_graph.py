from app.agents.graph import build_graph
from app.ingestion.pdf_loader import PDFLoader
from app.ingestion.chunker import TextChunker


PDF_PATH = "data/raw/employee_policy.pdf"


def build_chunks():
    loader = PDFLoader()
    documents = loader.load(PDF_PATH)

    chunker = TextChunker()
    return chunker.chunk_documents(documents)


def test_pdf_route():

    chunks = build_chunks()
    graph = build_graph(chunks)

    result = graph.invoke({
        "query": "How many annual leave days do employees receive?",
        "route": "pdf",
    })

    assert result["route"] == "pdf"
    assert result["answer"]
    assert result["evidence"]
    assert result["sources"]

    print("\nPDF ROUTE")
    print("=" * 60)
    print(result["answer"])

    print("\nEvidence:")
    print(result["evidence"])

    print("\nSources:")
    print(result["sources"])


def test_web_route():

    chunks = build_chunks()
    graph = build_graph(chunks)

    result = graph.invoke({
        "query": "What is the current website content?",
        "url": "https://example.com",
    })

    assert result["route"] == "web"
    assert result["answer"]
    assert result["evidence"]
    assert result["sources"]

    # Verify the actual retrieved webpage evidence
    assert "Example Domain" in result["evidence"][0]["text"]

    # Verify source information
    assert result["sources"][0]["url"] == "https://example.com"

    print("\nWEB ROUTE")
    print("=" * 60)
    print(result["answer"][:1000])

    print("\nEvidence:")
    print(result["evidence"][0]["text"][:1000])

    print("\nSources:")
    print(result["sources"])


def test_db_route():

    chunks = build_chunks()
    graph = build_graph(chunks)

    result = graph.invoke({
        "query": "Show me employee 104",
        "user_role": "hr",
    })

    assert result["route"] == "db"
    assert result["answer"]
    assert result["evidence"]
    assert result["sources"]

    # Verify database evidence
    assert result["evidence"][0]["employee_id"] == 104
    assert result["evidence"][0]["name"] == "Ananya Singh"
    assert result["evidence"][0]["department"] == "Engineering"
    assert result["evidence"][0]["role"] == "AI Engineer"

    # Verify database source
    assert result["sources"][0]["type"] == "database"
    assert result["sources"][0]["table"] == "employees"
    assert result["sources"][0]["employee_id"] == 104

    print("\nDB ROUTE")
    print("=" * 60)
    print(result["answer"])

    print("\nEvidence:")
    print(result["evidence"])

    print("\nSources:")
    print(result["sources"])


if __name__ == "__main__":

    test_pdf_route()
    test_web_route()
    test_db_route()

    print("\nMulti-agent LangGraph test passed.")


def test_pdf_graph_returns_grounded_answer():

    chunks = build_chunks()
    graph = build_graph(chunks)

    result = graph.invoke(
        {
            "query": "How many annual leave days do employees receive?",
            "user_role": "employee",
        }
    )

    assert result["route"] == "pdf"
    assert result["answer"]
    assert result["evidence"]
    assert result["sources"]

    # The answer should be grounded in the retrieved evidence.
    assert "24" in result["answer"]
    assert "annual leave" in result["answer"].lower()    