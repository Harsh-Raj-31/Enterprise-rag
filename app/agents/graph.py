from langgraph.graph import StateGraph, START, END

from app.agents.state import AgentState
from app.agents.router import query_router
from app.agents.pdf_agent import PDFAgent
from app.agents.web_agent import WebAgent
from app.agents.db_agent import DBAgent
from app.agents.spreadsheet_agent import SpreadsheetAgent


def build_graph(chunks: list[dict]):

    r"""
    Build the multi-agent LangGraph workflow.

        START
          |
        Router
       /  |  \
     PDF WEB  DB
      |   |    |
      v   v    v
    Agent Agent Agent
       \   |   /
          END
    """

    pdf_agent = PDFAgent(chunks)
    web_agent = WebAgent()
    db_agent = DBAgent()
    spreadsheet_agent = SpreadsheetAgent()

    graph = StateGraph(AgentState)

    graph.add_node("router", query_router)
    graph.add_node("pdf_agent", pdf_agent.run)
    graph.add_node("web_agent", web_agent.run)
    graph.add_node("db_agent", db_agent.run)

    graph.add_node(
        "spreadsheet_agent",
        spreadsheet_agent.run,
    )

    graph.add_edge(START, "router")

    graph.add_conditional_edges(
        "router",
        lambda state: state["route"],
        {
            "pdf": "pdf_agent",
            "web": "web_agent",
            "db": "db_agent",
            "spreadsheet": "spreadsheet_agent",
        },
    )

    graph.add_edge("pdf_agent", END)
    graph.add_edge("web_agent", END)
    graph.add_edge("db_agent", END)
    graph.add_edge(
    "spreadsheet_agent",
    END,
    )


    return graph.compile()
