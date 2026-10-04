from unittest.mock import Mock, patch

import pytest

from app.agents.web_agent import WebAgent


def test_web_agent():

    agent = WebAgent()

    state = {
        "query": "What does this webpage say?",
        "url": "https://example.com",
    }

    result = agent.run(state)

    assert result["answer"]
    assert result["evidence"]

    evidence_text = result["evidence"][0]["text"]

    assert "Example Domain" in evidence_text
    assert "documentation examples" in evidence_text

    assert result["sources"]
    assert result["sources"][0]["url"] == "https://example.com"

    print("\nWEB AGENT TEST")
    print("=" * 60)

    print("\nQuery:")
    print(state["query"])

    print("\nAnswer:")
    print(result["answer"])

    print("\nEvidence:")
    print(evidence_text[:1000])

    print("\nSources:")
    print(result["sources"])

    print("\nWeb Agent test passed.")


if __name__ == "__main__":
    test_web_agent()


def test_web_agent_blocks_non_http_url():

    agent = WebAgent()

    try:
        agent.validate_url(
            "file:///etc/passwd"
        )

        raise AssertionError(
            "ERROR: unsafe URL scheme was accepted"
        )

    except ValueError as exc:

        assert "HTTP and HTTPS" in str(exc)

        print(
            "\nUnsafe URL scheme blocked:"
        )
        print(exc)    


def test_web_agent_blocks_unsafe_redirect():
    agent = WebAgent()

    redirect_response = Mock()
    redirect_response.is_redirect = True
    redirect_response.is_permanent_redirect = False
    redirect_response.headers = {
        "Location": "http://localhost:8000/admin"
    }

    with patch(
        "app.agents.web_agent.requests.get",
        return_value=redirect_response,
    ):
        with pytest.raises(ValueError):
            agent.fetch_page("https://example.com")
