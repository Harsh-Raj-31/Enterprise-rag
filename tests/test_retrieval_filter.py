from app.security.models import User
from app.security.retrieval_filter import (
    filter_documents_by_role,
)
from app.retrieval.retriever import Retriever

def test_retrieval_filter():

    documents = [
        {
            "text": "General company policy",
            "metadata": {
                "source": "general_policy.pdf",
                "allowed_roles": [
                    "employee",
                    "manager",
                    "hr",
                    "admin",
                ],
            },
        },
        {
            "text": "Employee salary information",
            "metadata": {
                "source": "salary_database",
                "allowed_roles": [
                    "hr",
                    "admin",
                ],
            },
        },
        {
            "text": "Executive strategy",
            "metadata": {
                "source": "executive_documents",
                "allowed_roles": [
                    "admin",
                ],
            },
        },
    ]

    employee = User(
        user_id="EMP101",
        username="aarav",
        role="employee",
    )

    hr_user = User(
        user_id="HR201",
        username="priya",
        role="hr",
    )

    admin_user = User(
        user_id="ADM001",
        username="admin",
        role="admin",
    )

    employee_results = filter_documents_by_role(
        documents,
        employee,
    )

    hr_results = filter_documents_by_role(
        documents,
        hr_user,
    )

    admin_results = filter_documents_by_role(
        documents,
        admin_user,
    )

    assert len(employee_results) == 1
    assert (
        employee_results[0]["metadata"]["source"]
        == "general_policy.pdf"
    )

    assert len(hr_results) == 2
    assert {
        result["metadata"]["source"]
        for result in hr_results
    } == {
        "general_policy.pdf",
        "salary_database",
    }

    assert len(admin_results) == 3

    print("Employee documents:", len(employee_results))
    print("HR documents:", len(hr_results))
    print("Admin documents:", len(admin_results))

    print("\nRetrieval filter test passed.")


if __name__ == "__main__":
    test_retrieval_filter()

def test_vector_retrieval_role_filter():

    retriever = Retriever()

    employee_results = retriever.retrieve(
        query="What are the working hours?",
        top_k=5,
        allowed_roles=["employee"],
    )

    hr_results = retriever.retrieve(
        query="What are the working hours?",
        top_k=5,
        allowed_roles=["hr"],
    )

    admin_results = retriever.retrieve(
        query="What are the working hours?",
        top_k=5,
        allowed_roles=["admin"],
    )

    assert employee_results
    assert hr_results
    assert admin_results

    for result in employee_results:
        assert (
            "employee"
            in result["metadata"]["allowed_roles"]
        )

    for result in hr_results:
        assert (
            "hr"
            in result["metadata"]["allowed_roles"]
        )

    for result in admin_results:
        assert (
            "admin"
            in result["metadata"]["allowed_roles"]
        )

    print(
        "\nVector retrieval RBAC test passed."
    )    