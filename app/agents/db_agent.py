import re
import sqlite3

from app.agents.state import AgentState
from app.agents.result import AgentResult
from app.security.access_control import AccessController


class DBAgent:
    """
    Agent responsible for retrieving structured information
    from the enterprise database.

    Database operations are read-only and use parameterized
    SQL queries.

    Structured database results are formatted deterministically
    instead of requiring an LLM, ensuring exact database values
    are returned.
    """

    def __init__(
        self,
        database_path: str = "data/sample/enterprise.db",
    ):
        self.database_path = database_path
        self.access_controller = AccessController()

    # =========================================================
    # DATABASE CONNECTION
    # =========================================================

    def _connect(self):
        """
        Create a read-only SQLite connection.
        """
        return sqlite3.connect(
            f"file:{self.database_path}?mode=ro",
            uri=True,
        )

    # =========================================================
    # SCHEMA DISCOVERY
    # =========================================================

    def discover_schema(self) -> dict[str, list[dict]]:
        """
        Discover the database schema at runtime.

        Returns:
            {
                "employees": [
                    {
                        "name": "id",
                        "type": "INTEGER",
                        "primary_key": True,
                        "nullable": True
                    },
                    ...
                ]
            }
        """

        connection = self._connect()

        try:
            tables = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            ).fetchall()

            schema = {}

            for (table_name,) in tables:
                columns = connection.execute(
                    f"PRAGMA table_info([{table_name}])"
                ).fetchall()

                schema[table_name] = [
                    {
                        "name": column[1],
                        "type": column[2],
                        "nullable": not bool(column[3]),
                        "primary_key": bool(column[5]),
                    }
                    for column in columns
                ]

            return schema

        finally:
            connection.close()

    # =========================================================
    # DATABASE LOOKUPS
    # =========================================================

    def get_employee_by_id(
        self,
        employee_id: int,
    ) -> dict | None:
        """
        Retrieve one employee by ID using a parameterized query.
        """

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

    def get_employees_by_department(
        self,
        department: str,
    ) -> list[dict]:
        """
        Retrieve all employees belonging to a department.

        Department comparison is case-insensitive.
        """

        connection = self._connect()

        try:
            cursor = connection.execute(
                """
                SELECT id, name, department, role
                FROM employees
                WHERE LOWER(department) = LOWER(?)
                ORDER BY id
                """,
                (department.strip(),),
            )

            rows = cursor.fetchall()

            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "department": row[2],
                    "role": row[3],
                }
                for row in rows
            ]

        finally:
            connection.close()

    # =========================================================
    # QUERY EXTRACTION
    # =========================================================

    def _extract_employee_id(
        self,
        query: str,
    ) -> int | None:
        """
        Extract an employee ID from queries such as:

        - What is employee 104?
        - What is the record for employee 104?
        - Employee ID: 104
        - Show ID 104
        """

        match = re.search(
            r"\b(?:employee\s*(?:id)?|id)\s*[:#-]?\s*(\d+)\b",
            query,
            re.IGNORECASE,
        )

        if match:
            return int(match.group(1))

        return None

    def _extract_department(
        self,
        query: str,
    ) -> str | None:
        """
        Extract a department from queries such as:

        - Which employees are in Engineering?
        - Which employees are in Finance department?
        - Show employees from Human Resources department
        - Who works in Engineering?
        """

        query = query.strip()

        patterns = [
            # "Which employees are in Engineering?"
            # "Which employees are in Finance department?"
            (
                r"\b(?:which\s+)?(?:employees|people|staff)"
                r"\s+(?:are\s+)?in\s+(?:the\s+)?"
                r"(.+?)(?:\s+department)?[?!.]?$"
            ),

            # "Show employees from Human Resources department"
            (
                r"\b(?:show|find|get|list)?\s*"
                r"(?:employees|people|staff)"
                r"\s+from\s+(?:the\s+)?"
                r"(.+?)(?:\s+department)?[?!.]?$"
            ),

            # "Who works in Engineering?"
            (
                r"\bwho\s+works\s+in\s+(?:the\s+)?"
                r"(.+?)[?!.]?$"
            ),
        ]

        for pattern in patterns:
            match = re.search(
                pattern,
                query,
                re.IGNORECASE,
            )

            if match:
                department = match.group(1).strip()

                if department:
                    return department

        return None

    # =========================================================
    # ANSWER FORMATTERS
    # =========================================================

    def _format_employee_answer(
        self,
        employee: dict,
    ) -> str:
        """
        Format a single employee record deterministically.
        """

        return (
            f"Employee ID: {employee['id']}\n"
            f"Name: {employee['name']}\n"
            f"Department: {employee['department']}\n"
            f"Role: {employee['role']}"
        )

    def _format_department_answer(
        self,
        department: str,
        employees: list[dict],
    ) -> str:
        """
        Format a department employee list deterministically.
        """

        lines = [
            f"Employees in {department}:",
            "",
        ]

        for employee in employees:
            lines.append(
                f"- {employee['name']} "
                f"(Employee ID: {employee['id']}) "
                f"— {employee['role']}"
            )

        return "\n".join(lines)

    # =========================================================
    # MAIN AGENT
    # =========================================================

    def run(
        self,
        state: AgentState,
    ) -> AgentState:
        """
        Execute the database agent.

        Flow:

        1. Validate query
        2. Discover database schema
        3. Validate required table/columns
        4. Validate authenticated role
        5. Enforce RBAC
        6. Determine database lookup
        7. Execute parameterized query
        8. Build deterministic answer
        9. Return structured evidence and sources
        """

        query = state["query"].strip()

        if not query:
            raise ValueError(
                "Database query cannot be empty."
            )

        user_role = state.get("user_role")

        # -----------------------------------------------------
        # Runtime schema validation
        # -----------------------------------------------------

        schema = self.discover_schema()

        if "employees" not in schema:
            raise RuntimeError(
                "Required employees table was not found "
                "in the database."
            )

        required_columns = {
            "id",
            "name",
            "department",
            "role",
        }

        available_columns = {
            column["name"]
            for column in schema["employees"]
        }

        missing_columns = required_columns - available_columns

        if missing_columns:
            raise RuntimeError(
                "Required database columns are missing: "
                + ", ".join(sorted(missing_columns))
            )

        # -----------------------------------------------------
        # Authentication / RBAC
        # -----------------------------------------------------

        if not user_role:
            raise PermissionError(
                "Authenticated user role is required "
                "for database access."
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

        # -----------------------------------------------------
        # Lookup 1: Employee ID
        # -----------------------------------------------------

        employee_id = self._extract_employee_id(query)

        if employee_id is not None:

            employee = self.get_employee_by_id(
                employee_id
            )

            if employee is None:

                answer = (
                    f"No employee record was found "
                    f"for ID {employee_id}."
                )

                evidence = []

            else:

                answer = self._format_employee_answer(
                    employee
                )

                evidence = [
                    {
                        "employee_id": employee["id"],
                        "name": employee["name"],
                        "department": employee["department"],
                        "role": employee["role"],
                    }
                ]

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

        # -----------------------------------------------------
        # Lookup 2: Department
        # -----------------------------------------------------

        department = self._extract_department(query)

        if department is not None:

            employees = self.get_employees_by_department(
                department
            )

            if not employees:

                answer = (
                    f"No employees were found in the "
                    f"{department} department."
                )

                evidence = []

            else:

                answer = self._format_department_answer(
                    department,
                    employees,
                )

                evidence = [
                    {
                        "employee_id": employee["id"],
                        "name": employee["name"],
                        "department": employee["department"],
                        "role": employee["role"],
                    }
                    for employee in employees
                ]

            agent_result: AgentResult = {
                "source_type": "database",
                "answer": answer,
                "evidence": evidence,
                "sources": [
                    {
                        "type": "database",
                        "table": "employees",
                        "department": department,
                    }
                ],
            }

            return {
                **state,
                "answer": agent_result["answer"],
                "evidence": agent_result["evidence"],
                "sources": agent_result["sources"],
            }

        # -----------------------------------------------------
        # Unsupported database query
        # -----------------------------------------------------

        answer = (
            "I could not determine the database lookup "
            "required for this query."
        )

        return {
            **state,
            "answer": answer,
            "evidence": [],
            "sources": [],
        }
