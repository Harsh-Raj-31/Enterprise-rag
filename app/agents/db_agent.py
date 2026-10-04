import re
import sqlite3

from app.agents.state import AgentState
from app.agents.result import AgentResult
from app.services.answer_service import AnswerService
from app.security.access_control import AccessController


class DBAgent:
    """
    Agent responsible for retrieving structured
    information from the enterprise database.

    Database operations are read-only and use
    parameterized SQL queries.
    """

    def __init__(
        self,
        database_path: str = "data/sample/enterprise.db",
    ):
        self.database_path = database_path
        self.answer_service = AnswerService()
        self.access_controller = AccessController()

    def _connect(self):
        return sqlite3.connect(self.database_path)

    def get_employee_by_id(
        self,
        employee_id: int,
    ) -> dict | None:

        connection = self._connect()

        try:
            cursor = connection.execute(
                """
                SELECT id, name, department, role
                FROM employees
                WHERE id = ?
                """,
                (employee_id,),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return {
                "id": row[0],
                "name": row[1],
                "department": row[2],
                "role": row[3],
            }

        finally:
            connection.close()

    def _extract_employee_id(
        self,
        query: str,
    ) -> int | None:

        match = re.search(
            r"\b(?:employee\s*(?:id)?|id)\s*[:#-]?\s*(\d+)\b",
            query,
            re.IGNORECASE,
        )

        if match:
            return int(match.group(1))

        return None

    def run(
        self,
        state: AgentState,
    ) -> AgentState:

        query = state["query"].strip()

        user_role = state.get("user_role")

        if not user_role:
            raise PermissionError(
                "Authenticated user role is required for database access."
            )

        from app.security.models import User

        user = User(
            user_id="agent-user",
            username="agent-user",
            role=user_role,
        )

        self.access_controller.require_access(
            user=user,
            source="employee_records",
        )        

        employee_id = self._extract_employee_id(query)

        if employee_id is None:

            answer = (
                "Please provide a valid employee ID "
                "so I can retrieve the employee record."
            )

            agent_result: AgentResult = {
                "source_type": "database",
                "answer": answer,
                "evidence": [],
                "sources": [],
            }

            return {
                **state,
                "answer": agent_result["answer"],
                "evidence": agent_result["evidence"],
                "sources": agent_result["sources"],
            }

        employee = self.get_employee_by_id(employee_id)

        if employee is None:

            evidence = []

            answer = (
                f"No employee record was found "
                f"for ID {employee_id}."
            )

        else:

            evidence = [
                {
                    "employee_id": employee["id"],
                    "name": employee["name"],
                    "department": employee["department"],
                    "role": employee["role"],
                }
            ]

            answer = self.answer_service.generate(
                query=query,
                evidence=evidence,
                user_role=user_role,
            )

        agent_result: AgentResult = {
            "source_type": "database",
            "answer": answer,
            "evidence": evidence,
            "sources": [
                {
                    "type": "database",
                    "table": "employees",
                    "employee_id": employee_id,
                }
            ],
        }

        return {
            **state,
            "answer": agent_result["answer"],
            "evidence": agent_result["evidence"],
            "sources": agent_result["sources"],
        }