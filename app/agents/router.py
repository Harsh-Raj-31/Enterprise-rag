import re
from app.agents.state import AgentState


WEB_KEYWORDS = {
    "latest",
    "recent",
    "today",
    "current",
    "currently",
    "online",
    "website",
    "web",
    "internet",
    "news",
    "breaking",
    "updated",
    "update",
}

DB_KEYWORDS = {
    "database",
    "databases",
    "record",
    "records",
    "employee id",
    "sql",
    "table",
    "tables",
    "query database",
    "customer record",
    "user record",
}

SPREADSHEET_KEYWORDS = {
    "spreadsheet",
    "csv",
    "excel",
    "xlsx",
    "worksheet",
    "row",
    "rows",
    "column",
    "columns",
    "sheet",
    "sheets",
    "employee list",
    "employee directory",
    "staff list",
    "department list",
    "designation list",
}

PDF_KEYWORDS = {
    "document",
    "documents",
    "policy",
    "policies",
    "pdf",
    "knowledge base",
    "company policy",
    "employee policy",
    "manual",
    "guideline",
    "guidelines",
}

EMPLOYEE_DIRECTORY_KEYWORDS = {
    "who is the",
    "who is",
    "who works",
    "who works in",
    "which employee",
    "which employees",
}


def query_router(state: AgentState) -> AgentState:
    """
    Route the user query to the appropriate knowledge source.

    Priority:
    1. Employee ID query -> DB
    2. Explicit URL -> Web
    3. Web/current-information keywords -> Web
    4. Database keywords -> DB
    5. Spreadsheet / employee directory -> Spreadsheet
    . PDF/knowledge-base keywords -> PDF
    7. Default -> PDF
    """

    query = state["query"].strip().lower()
    url = state.get("url")

    # ---------------------------------------------------------
    # 1. Employee ID query -> Database
    # ---------------------------------------------------------
    if re.search(
        r"\b(?:employee\s*(?:id)?|id)\s*[:#-]?\s*\d+\b",
        query,
        re.IGNORECASE,
    ):
        route = "db"

    # ---------------------------------------------------------
    # 2. Explicit URL -> Web
    # ---------------------------------------------------------
    elif url or "http://" in query or "https://" in query or "www." in query:
        route = "web"
    # ---------------------------------------------------------
    # 3. Web / current information
    # ---------------------------------------------------------
    elif any(keyword in query for keyword in WEB_KEYWORDS):
        route = "web"

    # ---------------------------------------------------------
    # 4. Database / structured employee directory
    # ---------------------------------------------------------
    elif (
        any(keyword in query for keyword in DB_KEYWORDS)
        or any(
            phrase in query
            for phrase in EMPLOYEE_DIRECTORY_KEYWORDS
        )
    ):
        route = "db"

    # ---------------------------------------------------------
    # 5. PDF / Knowledge Base
    # ---------------------------------------------------------
    elif any(
        keyword in query
        for keyword in PDF_KEYWORDS
    ):
        route = "pdf"

    # ---------------------------------------------------------
    # 6. Spreadsheet / CSV / Excel
    # ---------------------------------------------------------
    elif any(
        keyword in query
        for keyword in SPREADSHEET_KEYWORDS
    ):
        route = "spreadsheet"

    # ---------------------------------------------------------
    # 7. Default
    # ---------------------------------------------------------
    else:
        route = "pdf"

    return {
        **state,
        "route": route,
    }
