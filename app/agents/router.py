import re

from app.agents.state import AgentState


# ---------------------------------------------------------
# Web / current-information keywords
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Database keywords
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Spreadsheet / CSV / Excel keywords
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# PDF / employee-policy / knowledge-base keywords
# ---------------------------------------------------------

PDF_KEYWORDS = {
    # Explicit document references
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

    # Common employee-policy questions
    "annual leave",
    "leave days",
    "paid leave",
    "sick leave",
    "maternity leave",
    "paternity leave",
    "vacation days",
    "employee benefits",
    "working hours",
    "work hours",
    "attendance policy",
    "leave policy",
    "holiday policy",
    "employee handbook",
    "company rules",
}


# ---------------------------------------------------------
# Employee-directory query phrases
# ---------------------------------------------------------

EMPLOYEE_DIRECTORY_KEYWORDS = {
    "who is the",
    "who is",
    "who works",
    "who works in",
    "which employee",
    "which employees",
}


def contains_keyword(
    query: str,
    keywords: set[str],
) -> bool:
    """
    Match keywords without accidentally matching
    partial words.

    Single words use word boundaries.
    Multiword phrases use substring matching.
    """

    for keyword in keywords:
        keyword = keyword.lower().strip()

        if not keyword:
            continue

        if " " in keyword:
            if keyword in query:
                return True

        else:
            pattern = (
                r"\b"
                + re.escape(keyword)
                + r"\b"
            )

            if re.search(pattern, query):
                return True

    return False


def query_router(
    state: AgentState,
) -> AgentState:
    """
    Route a query to the appropriate knowledge source.

    Priority:
    1. Employee ID queries -> Database
    2. Explicit URL -> Web
    3. Database / employee-directory queries -> Database
    4. Spreadsheet queries -> Spreadsheet
    5. Explicit document / employee-policy queries -> PDF
    6. Current-information / web queries -> Web
    7. Default -> Web

    The default Web route supports retrieval from
    previously ingested websites when no URL is supplied.
    """

    query = state["query"].strip().lower()
    url = state.get("url")

    # ---------------------------------------------------------
    # 1. Employee ID query -> Database
    # ---------------------------------------------------------

    if re.search(
        r"\b(?:employee\s*(?:id)?|id)\s*[:#-]?\s*\d+\b",
        query,
    ):
        route = "db"

    # ---------------------------------------------------------
    # 2. Explicit URL -> Web
    # ---------------------------------------------------------

    elif (
        url
        or re.search(
            r"https?://|www\.",
            query,
        )
    ):
        route = "web"

    # ---------------------------------------------------------
    # 3. Database / structured employee-directory queries
    # ---------------------------------------------------------

    elif (
        contains_keyword(
            query,
            DB_KEYWORDS,
        )
        or contains_keyword(
            query,
            EMPLOYEE_DIRECTORY_KEYWORDS,
        )
    ):
        route = "db"

    # ---------------------------------------------------------
    # 4. Spreadsheet / CSV / Excel queries
    # ---------------------------------------------------------

    elif contains_keyword(
        query,
        SPREADSHEET_KEYWORDS,
    ):
        route = "spreadsheet"

    # ---------------------------------------------------------
    # 5. PDF / employee-policy / knowledge-base queries
    # ---------------------------------------------------------

    elif contains_keyword(
        query,
        PDF_KEYWORDS,
    ):
        route = "pdf"

    # ---------------------------------------------------------
    # 6. Web / current-information queries
    # ---------------------------------------------------------

    elif contains_keyword(
        query,
        WEB_KEYWORDS,
    ):
        route = "web"

    # ---------------------------------------------------------
    # 7. Default -> Web
    # ---------------------------------------------------------

    else:
        route = "web"

    return {
        **state,
        "route": route,
    }