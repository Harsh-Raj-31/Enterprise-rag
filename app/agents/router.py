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


def query_router(state: AgentState) -> AgentState:
    """
    Route the user query to the appropriate knowledge source.

    Priority:
    1. Employee ID query -> DB
    2. Explicit URL -> Web
    3. Web/current-information keywords -> Web
    4. Database keywords -> DB
    5. PDF/knowledge-base keywords -> PDF
    6. Default -> PDF
    """

    query = state["query"].strip().lower()

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
    elif "http://" in query or "https://" in query or "www." in query:
        route = "web"

    # ---------------------------------------------------------
    # 3. Web / current information
    # ---------------------------------------------------------
    elif any(keyword in query for keyword in WEB_KEYWORDS):
        route = "web"

    # ---------------------------------------------------------
    # 4. Database
    # ---------------------------------------------------------
    elif any(keyword in query for keyword in DB_KEYWORDS):
        route = "db"

    # ---------------------------------------------------------
    # 5. PDF / Knowledge Base
    # ---------------------------------------------------------
    elif any(keyword in query for keyword in PDF_KEYWORDS):
        route = "pdf"

    # ---------------------------------------------------------
    # 6. Default
    # ---------------------------------------------------------
    else:
        route = "pdf"

    return {
        **state,
        "route": route,
    }