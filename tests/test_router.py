from app.agents.router import query_router


def test_pdf_route():
    test_cases = [
        "How many annual leave days do employees receive?",
        "What does the employee policy say about working hours?",
        "Show me the company PDF policy",
        "What is the work from home policy?",
        "Tell me about the knowledge base documents",
    ]

    for query in test_cases:
        result = query_router({"query": query})
        assert result["route"] == "pdf", query


def test_web_route():
    test_cases = [
        "What is the latest company news?",
        "What happened today?",
        "Show me the current information online",
        "What is available on the company website?",
        "https://example.com",
        "www.example.com",
    ]

    for query in test_cases:
        result = query_router({"query": query})
        assert result["route"] == "web", query


def test_database_route():
    test_cases = [
        "Show me the employee database records",
        "Find the employee record",
        "Run this SQL query",
        "Show me the customer records",
        "Query the database",
    ]

    for query in test_cases:
        result = query_router({"query": query})
        assert result["route"] == "db", query


def test_default_route():
    result = query_router({
        "query": "How many days of leave are available?"
    })

    assert result["route"] == "pdf"


if __name__ == "__main__":
    test_pdf_route()
    test_web_route()
    test_database_route()
    test_default_route()

    print("\nAll router tests passed.")