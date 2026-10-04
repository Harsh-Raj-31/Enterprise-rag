import sqlite3
from pathlib import Path


DATABASE_PATH = Path("data/sample/enterprise.db")


def create_database():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        connection.execute("DROP TABLE IF EXISTS employees")

        connection.execute(
            """
            CREATE TABLE employees (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                role TEXT NOT NULL
            )
            """
        )

        employees = [
            (101, "Aarav Sharma", "Engineering", "Software Engineer"),
            (102, "Priya Verma", "Human Resources", "HR Manager"),
            (103, "Rohan Mehta", "Finance", "Financial Analyst"),
            (104, "Ananya Singh", "Engineering", "AI Engineer"),
            (105, "Vikram Kumar", "Sales", "Sales Executive"),
        ]

        connection.executemany(
            """
            INSERT INTO employees
            (id, name, department, role)
            VALUES (?, ?, ?, ?)
            """,
            employees,
        )

        connection.commit()

    finally:
        connection.close()

    print(f"Database created successfully: {DATABASE_PATH}")


if __name__ == "__main__":
    create_database()