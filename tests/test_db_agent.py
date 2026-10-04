from app.agents.db_agent import DBAgent


def test_db_agent():

    agent = DBAgent()

    state = {
        "query": "Show me employee 104",
        "user_role": "hr",
    }

    result = agent.run(state)

    assert result["answer"]
    assert result["evidence"]
    assert result["sources"]

    evidence = result["evidence"][0]

    assert evidence["employee_id"] == 104
    assert evidence["name"] == "Ananya Singh"
    assert evidence["department"] == "Engineering"
    assert evidence["role"] == "AI Engineer"

    source = result["sources"][0]

    assert source["type"] == "database"
    assert source["table"] == "employees"
    assert source["employee_id"] == 104

    print("\nDB AGENT TEST")
    print("=" * 60)

    print("\nQuery:")
    print(state["query"])

    print("\nAnswer:")
    print(result["answer"])

    print("\nEvidence:")
    print(result["evidence"])

    print("\nSources:")
    print(result["sources"])

    print("\nDB Agent test passed.")


if __name__ == "__main__":
    test_db_agent()


def test_db_agent_blocks_unauthorized_role():

    agent = DBAgent()

    state = {
        "query": "Show me employee 104",
        "user_role": "employee",
    }

    try:
        agent.run(state)

        raise AssertionError(
            "ERROR: unauthorized database access was granted"
        )

    except PermissionError as exc:

        assert "employee_records" in str(exc)

        print(
            "\nUnauthorized DB access blocked:"
        )
        print(exc)