from app.agents.graph import build_graph
from app.ingestion.pdf_loader import PDFLoader
from app.ingestion.chunker import TextChunker


class GraphService:
    """
    Builds and owns the reusable LangGraph instance.
    """

    def __init__(self):
        chunks = self._load_chunks()
        self.graph = build_graph(chunks)

    def _load_chunks(self) -> list[dict]:
        pdf_path = "data/raw/employee_policy.pdf"

        loader = PDFLoader()
        documents = loader.load(pdf_path)

        chunker = TextChunker()
        return chunker.chunk_documents(documents)

    def invoke(
        self,
        query: str,
        user_role: str,
    ) -> dict:
        return self.graph.invoke({
            "query": query,
            "user_role": user_role,
        })