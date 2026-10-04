import html
import time
from pathlib import Path

import streamlit as st

from app.core.config import MODEL
from app.ingestion.pdf_loader import PDFLoader
from app.ingestion.chunker import TextChunker
from app.services.rag_service import RAGService


# ===========================================================
# PAGE CONFIGURATION
# ===========================================================

st.set_page_config(
    page_title="Enterprise Knowledge Base",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ===========================================================
# CONSTANTS
# ===========================================================

UPLOAD_DIR = Path("data/raw/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ===========================================================
# SESSION STATE
# ===========================================================

defaults = {
    "history": [],
    "active_pdf_path": None,
    "indexed_document_name": None,
    "index_success_message": None,
    "pdf_file_version": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ===========================================================
# GLOBAL STYLING — Modern SaaS dashboard
#
#   - Light neutral canvas, white elevated cards
#   - Distinct accent color per metric/section (like a real
#     analytics dashboard: indigo / emerald / amber / rose)
#   - Rounded-xl cards, soft shadows, colored icon chips
#   - Dark sidebar acting as the "nav rail"
# ===========================================================

st.markdown(
    """
<style>

:root {
    --canvas: #f4f5fa;
    --card: #ffffff;
    --border: #e7e9f3;

    --text-primary: #171923;
    --text-secondary: #5a5f78;
    --text-muted: #8b90a8;

    --indigo: #5b5bf0;
    --indigo-soft: #edeeff;
    --emerald: #12b886;
    --emerald-soft: #e5fbf3;
    --amber: #f5a524;
    --amber-soft: #fef3dd;
    --rose: #ef5da8;
    --rose-soft: #fdeaf3;
    --sky: #2f9ce0;
    --sky-soft: #e6f5fd;

    --danger: #e5484d;
    --danger-soft: #fdecec;

    --shadow-card: 0 1px 2px rgba(23,25,35,0.04), 0 8px 24px -12px rgba(23,25,35,0.10);
    --radius-xl: 20px;
    --radius-lg: 16px;
    --radius-md: 12px;
}

.stApp { background: var(--canvas); }

#MainMenu, header, footer { visibility: hidden; }

.block-container {
    padding-top: 1.8rem;
    max-width: 1180px;
}

html, body, [class*="css"] { font-size: 15.5px; line-height: 1.55; }

section[data-testid="stMain"] p,
section[data-testid="stMain"] li,
div[data-testid="stMarkdownContainer"] p {
    color: var(--text-primary) !important;
}

section[data-testid="stMain"] strong,
section[data-testid="stMain"] h1,
section[data-testid="stMain"] h2,
section[data-testid="stMain"] h3,
section[data-testid="stMain"] h4 {
    color: var(--text-primary) !important;
}


/* =========================================================
   TOP BAR / HERO
   ========================================================= */

.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 1.1rem 1.6rem;
    border-radius: var(--radius-xl);
    background: var(--card);
    border: 1px solid var(--border);
    box-shadow: var(--shadow-card);
    margin-bottom: 1.4rem;
}

.topbar-left { display: flex; align-items: center; gap: 0.9rem; }

.topbar-icon {
    width: 46px; height: 46px;
    border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.5rem;
    background: linear-gradient(135deg, var(--indigo) 0%, #8f7bf5 100%);
    box-shadow: 0 6px 16px -6px rgba(91,91,240,0.55);
}

section[data-testid="stMain"] .topbar-title {
    color: var(--text-primary) !important;
    font-size: 1.35rem;
    font-weight: 800;
    letter-spacing: -0.01em;
    margin: 0;
}

section[data-testid="stMain"] .topbar-subtitle {
    color: var(--text-muted) !important;
    font-size: 0.86rem;
    margin: 0.1rem 0 0 0;
}

.status-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.4rem 0.85rem;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 700;
}

.status-chip.online {
    background: var(--emerald-soft);
    color: var(--emerald) !important;
}

.status-chip.offline {
    background: var(--amber-soft);
    color: var(--amber) !important;
}

.status-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: currentColor;
}


/* =========================================================
   FEATURE PILLS
   ========================================================= */

.pill-row { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1.5rem; }

.pill {
    display: inline-flex; align-items: center; gap: 0.35rem;
    padding: 0.32rem 0.78rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 700;
    border: 1px solid var(--border);
    background: var(--card);
    color: var(--text-secondary) !important;
}


/* =========================================================
   SECTION CARD (generic elevated container)
   ========================================================= */

.section-card {
    padding: 1.3rem 1.5rem;
    border-radius: var(--radius-lg);
    background: var(--card);
    border: 1px solid var(--border);
    box-shadow: var(--shadow-card);
    margin-bottom: 1rem;
}

.section-eyebrow {
    display: flex; align-items: center; gap: 0.5rem;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--indigo) !important;
    margin-bottom: 0.3rem;
}

.section-title {
    font-size: 1.08rem;
    font-weight: 800;
    color: var(--text-primary) !important;
    margin-bottom: 0.15rem;
}

.section-subtitle {
    font-size: 0.87rem;
    color: var(--text-muted) !important;
    margin: 0;
}

.selected-file {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.55rem 0.9rem;
    margin: 0.7rem 0;
    border-radius: var(--radius-md);
    background: var(--emerald-soft);
    border: 1px solid #bdf0dd;
    color: var(--emerald) !important;
    font-size: 0.87rem;
    font-weight: 600;
}


/* =========================================================
   EMPTY STATE
   ========================================================= */

.empty-state {
    text-align: center;
    padding: 1.6rem 1rem;
    color: var(--text-muted) !important;
    font-size: 0.92rem;
    background: var(--canvas);
    border: 1.5px dashed var(--border);
    border-radius: var(--radius-lg);
}


/* =========================================================
   STAT / METRIC CARDS — colored per metric like a dashboard
   ========================================================= */

.stat-card {
    display: flex;
    align-items: center;
    gap: 0.85rem;
    padding: 1rem 1.1rem;
    border-radius: var(--radius-lg);
    background: var(--card);
    border: 1px solid var(--border);
    box-shadow: var(--shadow-card);
    min-height: 78px;
}

.stat-icon {
    width: 42px; height: 42px;
    min-width: 42px;
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.2rem;
}

.stat-icon.indigo { background: var(--indigo-soft); }
.stat-icon.emerald { background: var(--emerald-soft); }
.stat-icon.amber { background: var(--amber-soft); }
.stat-icon.rose { background: var(--rose-soft); }

.stat-value {
    font-size: 1.3rem;
    font-weight: 800;
    color: var(--text-primary) !important;
    line-height: 1.1;
    word-break: break-word;
}

.stat-label {
    font-size: 0.74rem;
    color: var(--text-muted) !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-top: 0.1rem;
}


/* =========================================================
   ARCHITECTURE (sidebar)
   ========================================================= */

.arch-step {
    display: flex; align-items: center; gap: 0.6rem;
    padding: 0.5rem 0.7rem;
    border-radius: 10px;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.10);
    margin-bottom: 0.3rem;
    font-size: 0.84rem;
    font-weight: 600;
}

.arch-step .step-num {
    display: inline-flex; align-items: center; justify-content: center;
    width: 20px; height: 20px;
    border-radius: 6px;
    background: var(--indigo);
    color: white;
    font-size: 0.7rem;
    font-weight: 800;
}

.arch-arrow { text-align: center; color: #5a5f78 !important; font-size: 0.85rem; margin: -0.1rem 0 0.2rem 0; }


/* =========================================================
   ANSWER
   ========================================================= */

.answer-card {
    padding: 1.3rem 1.6rem;
    border-radius: var(--radius-lg);
    background: linear-gradient(180deg, var(--indigo-soft) 0%, var(--card) 65%);
    border: 1px solid var(--border);
    box-shadow: var(--shadow-card);
    margin-bottom: 0.9rem;
}

.answer-heading {
    font-size: 0.95rem;
    font-weight: 800;
    color: var(--indigo) !important;
    display: flex; align-items: center; gap: 0.45rem;
    margin-bottom: 0.6rem;
}

.response-time { font-weight: 600; color: var(--text-muted) !important; font-size: 0.78rem; }


/* =========================================================
   SOURCES
   ========================================================= */

.sources-title {
    display: flex; align-items: center; gap: 0.5rem;
    font-size: 1.05rem;
    font-weight: 800;
    color: var(--text-primary) !important;
    margin-top: 22px;
    margin-bottom: 12px;
}

.source-card {
    padding: 0.9rem 1.1rem;
    border-radius: var(--radius-md);
    border: 1px solid var(--border);
    border-left: 4px solid var(--indigo);
    background: var(--card);
    box-shadow: var(--shadow-card);
    margin-bottom: 0.6rem;
}

.source-title { font-weight: 700; color: var(--text-primary) !important; font-size: 0.9rem; margin-bottom: 0.35rem; }

.source-meta {
    display: flex; flex-wrap: wrap; gap: 0.8rem; align-items: center;
    font-size: 0.82rem;
    color: var(--text-secondary) !important;
}


/* =========================================================
   RERANKER SCORES
   ========================================================= */

.score-badge {
    display: inline-block;
    padding: 0.12rem 0.6rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 800;
}

.score-positive { background: var(--emerald-soft); color: var(--emerald) !important; }
.score-negative { background: var(--danger-soft); color: var(--danger) !important; }


/* =========================================================
   SIDEBAR — dark nav rail
   ========================================================= */

section[data-testid="stSidebar"] { background: #13141d; }
section[data-testid="stSidebar"] * { color: #e7e8f2 !important; }
section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.10) !important; }


/* =========================================================
   INPUTS / BUTTONS
   ========================================================= */

.stTextInput input {
    border-radius: var(--radius-md) !important;
    padding: 0.68rem 1rem !important;
    border: 1.5px solid var(--border) !important;
    color: var(--text-primary) !important;
    background: var(--card) !important;
}

.stTextInput input::placeholder { color: var(--text-muted) !important; }

.stTextInput input:focus {
    border-color: var(--indigo) !important;
    box-shadow: 0 0 0 3px var(--indigo-soft) !important;
}

.stButton button {
    border-radius: var(--radius-md) !important;
    font-weight: 800 !important;
    padding: 0.62rem 1.3rem !important;
    border: none !important;
}

div[data-testid="stButton"] button[kind="primary"] {
    background: linear-gradient(135deg, var(--indigo) 0%, #8f7bf5 100%) !important;
    box-shadow: 0 6px 16px -6px rgba(91,91,240,0.55) !important;
}


/* =========================================================
   FILE UPLOADER
   ========================================================= */

div[data-testid="stFileUploader"] { margin-bottom: 0.5rem; }

div[data-testid="stFileUploaderDropzone"] {
    border-radius: var(--radius-md) !important;
    border: 1.5px dashed #c7cae8 !important;
    background: #fafaff !important;
}


/* =========================================================
   ALERTS / EXPANDER
   ========================================================= */

div[data-testid="stAlert"] { color: var(--text-primary) !important; border-radius: var(--radius-md) !important; }

section[data-testid="stMain"] div[data-testid="stExpander"],
section[data-testid="stMain"] div[data-testid="stExpander"] p {
    color: var(--text-primary) !important;
}

section[data-testid="stMain"] div[data-testid="stExpander"] {
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--border) !important;
    box-shadow: var(--shadow-card);
}

</style>
""",
    unsafe_allow_html=True,
)


# ===========================================================
# RAG SERVICE LOADER
# ===========================================================

@st.cache_resource(show_spinner=False)
def load_rag_service(pdf_path: str, file_version: int):
    """
    Build a RAG service for the selected PDF.
    file_version forces a rebuild if a same-named file is replaced.
    """

    loader = PDFLoader()
    documents = loader.load(pdf_path)

    if not documents:
        raise ValueError("The PDF contains no extractable text.")

    chunker = TextChunker(chunk_size=120, chunk_overlap=20)
    chunks = chunker.chunk_documents(documents)

    if not chunks:
        raise ValueError("No chunks were generated from the PDF.")

    rag_service = RAGService(chunks)
    return rag_service, len(chunks)


# ===========================================================
# TOP BAR
# ===========================================================

is_online = st.session_state.active_pdf_path is not None
status_class = "online" if is_online else "offline"
status_label = "Knowledge Base Online" if is_online else "Awaiting Document"

st.markdown(
    f"""
<div class="topbar">
<div class="topbar-left">
<div class="topbar-icon">🧠</div>
<div>
<p class="topbar-title">Enterprise Knowledge Base</p>
<p class="topbar-subtitle">Hybrid retrieval &middot; cross-encoder reranking &middot; grounded answers with {html.escape(MODEL)}</p>
</div>
</div>
<div class="status-chip {status_class}"><span class="status-dot"></span>{status_label}</div>
</div>
""",
    unsafe_allow_html=True,
)


# ===========================================================
# FEATURE PILLS
# ===========================================================

st.markdown(
    f"""
<div class="pill-row">
<span class="pill">🔍 Vector Search</span>
<span class="pill">🔤 BM25</span>
<span class="pill">🧬 Hybrid Retrieval</span>
<span class="pill">🎯 Cross-Encoder Reranking</span>
<span class="pill">📄 PDF Ingestion</span>
<span class="pill">🤖 {html.escape(MODEL)}</span>
<span class="pill">✅ Grounded Answers</span>
</div>
""",
    unsafe_allow_html=True,
)


# ===========================================================
# PDF UPLOAD SECTION
# ===========================================================

st.markdown(
    """
<div class="section-card">
<div class="section-eyebrow">📥 Step 1</div>
<div class="section-title">Add Document to Knowledge Base</div>
<p class="section-subtitle">Upload a PDF, index it, then ask questions about its contents.</p>
</div>
""",
    unsafe_allow_html=True,
)

uploaded_file = st.file_uploader(
    "Upload PDF document",
    type=["pdf"],
    help="Upload a PDF document to create a searchable knowledge base.",
)


# ===========================================================
# PDF INDEXING
# ===========================================================

if uploaded_file is not None:

    safe_filename = Path(uploaded_file.name).name

    st.markdown(
        f"""<div class="selected-file">📄 {html.escape(safe_filename)}</div>""",
        unsafe_allow_html=True,
    )

    do_index = st.button("🚀 Index PDF", type="primary")

    if do_index:
        try:
            destination = UPLOAD_DIR / safe_filename

            with open(destination, "wb") as file:
                file.write(uploaded_file.getbuffer())

            loader = PDFLoader()
            test_documents = loader.load(str(destination))

            if not test_documents:
                raise ValueError("The PDF contains no extractable text.")

            file_version = destination.stat().st_mtime_ns

            st.session_state.active_pdf_path = str(destination)
            st.session_state.indexed_document_name = safe_filename
            st.session_state.pdf_file_version = file_version
            st.session_state.history = []
            st.session_state.index_success_message = (
                f"Successfully indexed '{safe_filename}'."
            )

            st.rerun()

        except Exception as error:
            st.error(f"Unable to index PDF: {error}")


# ===========================================================
# SUCCESS MESSAGE
# ===========================================================

if st.session_state.index_success_message:
    st.success(st.session_state.index_success_message)
    st.session_state.index_success_message = None


# ===========================================================
# KNOWLEDGE BASE STATUS
# ===========================================================

active_pdf_path = st.session_state.active_pdf_path
active_document_name = st.session_state.indexed_document_name


if active_pdf_path is None:
    chunk_count = 0
    rag_service = None

    st.markdown(
        """
<div class="empty-state">
📚 No document is currently indexed.<br>Upload a PDF above to create your knowledge base.
</div>
""",
        unsafe_allow_html=True,
    )

else:
    active_path = Path(active_pdf_path)

    if not active_path.exists():
        st.session_state.active_pdf_path = None
        st.session_state.indexed_document_name = None
        st.rerun()

    file_version = st.session_state.get(
        "pdf_file_version", active_path.stat().st_mtime_ns
    )

    with st.spinner("Preparing the knowledge base..."):
        rag_service, chunk_count = load_rag_service(str(active_path), file_version)


# ===========================================================
# STAT CARDS
# ===========================================================

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(
        f"""
<div class="stat-card">
<div class="stat-icon indigo">🧩</div>
<div><div class="stat-value">{chunk_count}</div><div class="stat-label">Knowledge Chunks</div></div>
</div>
""",
        unsafe_allow_html=True,
    )

with m2:
    document_count = 1 if active_pdf_path else 0
    st.markdown(
        f"""
<div class="stat-card">
<div class="stat-icon emerald">📄</div>
<div><div class="stat-value">{document_count}</div><div class="stat-label">Documents</div></div>
</div>
""",
        unsafe_allow_html=True,
    )

with m3:
    st.markdown(
        f"""
<div class="stat-card">
<div class="stat-icon amber">🤖</div>
<div><div class="stat-value" style="font-size:0.98rem;">{html.escape(MODEL)}</div><div class="stat-label">LLM</div></div>
</div>
""",
        unsafe_allow_html=True,
    )

with m4:
    questions_metric = st.empty()
    questions_metric.markdown(
        f"""
<div class="stat-card">
<div class="stat-icon rose">💬</div>
<div><div class="stat-value">{len(st.session_state.history)}</div><div class="stat-label">Questions Asked</div></div>
</div>
""",
        unsafe_allow_html=True,
    )

st.write("")


# ===========================================================
# SIDEBAR — nav rail
# ===========================================================

with st.sidebar:

    st.header("📚 Knowledge Base")

    if active_pdf_path:
        st.success("Knowledge Base Online")
        st.divider()
        st.markdown("**Current Document**")
        st.markdown(f"📄 `{html.escape(active_document_name)}`")
        st.markdown("**Knowledge Chunks**")
        st.markdown(f"`{chunk_count}`")

        if st.button("🗑️ Clear Knowledge Base", use_container_width=True):
            st.session_state.active_pdf_path = None
            st.session_state.indexed_document_name = None
            st.session_state.pdf_file_version = None
            st.session_state.history = []
            load_rag_service.clear()
            st.rerun()

    else:
        st.info("No document indexed yet.")
        st.markdown("Upload a PDF from the main page to initialize the knowledge base.")

    st.divider()

    st.header("🏗️ Architecture")

    steps = [
        "PDF Upload",
        "PDF Processing",
        "Smart Chunking",
        "Hybrid Retrieval",
        "Cross-Encoder Reranker",
        "Grounded Context",
        "LiteLLM Gateway",
        MODEL,
        "Answer + Sources",
    ]

    for i, step in enumerate(steps):
        st.markdown(
            f"""<div class="arch-step"><span class="step-num">{i + 1}</span>{html.escape(step)}</div>""",
            unsafe_allow_html=True,
        )
        if i != len(steps) - 1:
            st.markdown('<div class="arch-arrow">↓</div>', unsafe_allow_html=True)

    if st.session_state.history:
        st.divider()
        st.header("🕘 Recent Questions")

        for past_q in reversed(st.session_state.history[-5:]):
            st.markdown(f"- {html.escape(past_q)}")


# ===========================================================
# QUERY INTERFACE
# ===========================================================

st.markdown(
    """
<div class="section-card" style="margin-bottom: 0.8rem;">
<div class="section-eyebrow">💬 Step 2</div>
<div class="section-title">Ask the Knowledge Base</div>
<p class="section-subtitle">Ask a question and get a grounded answer with cited sources.</p>
</div>
""",
    unsafe_allow_html=True,
)

col_input, col_button = st.columns([5, 1])

with col_input:
    query = st.text_input(
        "Enter your question",
        placeholder=(
            "Upload and index a PDF first..."
            if rag_service is None
            else "e.g. What is the leave policy?"
        ),
        label_visibility="collapsed",
        disabled=(rag_service is None),
    )

with col_button:
    ask_button = st.button(
        "🔍 Ask",
        type="primary",
        use_container_width=True,
        disabled=(rag_service is None),
    )


def score_class(score: float) -> str:
    # Cross-encoder scores are raw relevance scores, not probabilities.
    return "score-positive" if score >= 0 else "score-negative"


# ===========================================================
# ANSWER GENERATION
# ===========================================================

if ask_button:

    if not query.strip():
        st.warning("Please enter a question.")

    elif rag_service is None:
        st.warning("Please upload and index a PDF first.")

    else:
        with st.spinner("Searching knowledge base..."):
            try:
                start = time.time()
                result = rag_service.answer(query=query, top_k=3)
                elapsed = time.time() - start

                st.session_state.history.append(query.strip())

                questions_metric.markdown(
                    f"""
<div class="stat-card">
<div class="stat-icon rose">💬</div>
<div><div class="stat-value">{len(st.session_state.history)}</div><div class="stat-label">Questions Asked</div></div>
</div>
""",
                    unsafe_allow_html=True,
                )

                st.divider()

                answer_html = (
                    f"""<div class="answer-heading">💡 <span>Answer</span>"""
                    f"""<span class="response-time">({elapsed:.2f}s)</span></div>"""
                )

                st.markdown(f"""<div class="answer-card">{answer_html}""", unsafe_allow_html=True)
                st.markdown(result["answer"])
                st.markdown("</div>", unsafe_allow_html=True)

                st.markdown(
                    """<div class="sources-title">📚 Sources</div>""",
                    unsafe_allow_html=True,
                )

                for index, source in enumerate(result["sources"], start=1):
                    score = float(source["rerank_score"])
                    badge_class = score_class(score)

                    source_name = html.escape(str(source.get("source", "Unknown source")))
                    page = html.escape(str(source.get("page", "Unknown")))
                    chunk_id = html.escape(str(source.get("chunk_id", "Unknown")))

                    st.markdown(
                        f"""
<div class="source-card">
<div class="source-title">Source {index} — {source_name}</div>
<div class="source-meta">
<span>📑 Page {page}</span>
<span>🔗 Chunk {chunk_id}</span>
<span class="score-badge {badge_class}">🎯 {score:.4f}</span>
</div>
</div>
""",
                        unsafe_allow_html=True,
                    )

                with st.expander("🔎 How this answer was generated"):
                    st.markdown(
                        f"""
**Current document:** `{active_document_name}`

**Pipeline**

1. PDF document
2. PDF text extraction
3. Intelligent chunking
4. Vector similarity search
5. BM25 keyword retrieval
6. Hybrid result combination
7. Cross-encoder reranking
8. Relevant evidence selection
9. {MODEL} generation
10. Answer with source references

**Response time:** `{elapsed:.2f} seconds`

**Evidence returned:** `{len(result["sources"])} sources`

**LLM:** `{MODEL}`

**Gateway:** `LiteLLM`
"""
                    )

            except Exception as error:
                st.error(f"Unable to generate answer: {error}")

elif rag_service is None:
    st.info("📄 Upload and index a PDF above to start asking questions.")