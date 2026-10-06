import html
import re
import time
from pathlib import Path

import streamlit as st

from app.core.config import MODEL
from app.ingestion.pdf_loader import PDFLoader
from app.ingestion.chunker import TextChunker
from app.services.rag_service import RAGService
from app.ui.api_client import APIClient


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

MAX_UPLOAD_MB = 50
CHUNK_SIZE = 120
CHUNK_OVERLAP = 20


# ============================================================
# SESSION STATE
# ============================================================

DEFAULTS = {
    "history": [],
    "last_result": None,          # persisted so the answer survives reruns
    "active_pdf_path": None,
    "indexed_document_name": None,
    "index_success_message": None,
    "pdf_file_version": None,

    # FastAPI authentication
    "access_token": None,
    "username": None,
    "user_role": None,
    "auth_notice": None,
}

for _key, _value in DEFAULTS.items():
    if _key not in st.session_state:
        st.session_state[_key] = list(_value) if isinstance(_value, list) else _value


def esc(value) -> str:
    """Escape any value rendered inside raw HTML."""
    return html.escape(str(value), quote=True)


# ============================================================
# API CLIENT
# ============================================================

@st.cache_resource(show_spinner=False)
def get_api_client() -> APIClient:
    return APIClient()


api_client = get_api_client()


# ===========================================================
# GLOBAL STYLING — Modern SaaS dashboard
# ===========================================================

CSS = """
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

#MainMenu, footer { visibility: hidden; }

/* Keep Streamlit's native header so the sidebar toggle remains available. */
header[data-testid="stHeader"],
header[data-testid="stHeader"] > div,
header[data-testid="stHeader"] [data-testid="stToolbar"] {
    background: transparent !important;
    box-shadow: none !important;
}

header[data-testid="stHeader"] { position: relative !important; z-index: 100 !important; }

.block-container { padding-top: 1.8rem; max-width: 1180px; }

html, body, [class*="css"] { font-size: 15.5px; line-height: 1.55; }

section[data-testid="stMain"] p,
section[data-testid="stMain"] li,
div[data-testid="stMarkdownContainer"] p { color: var(--text-primary) !important; }

section[data-testid="stMain"] strong,
section[data-testid="stMain"] h1,
section[data-testid="stMain"] h2,
section[data-testid="stMain"] h3,
section[data-testid="stMain"] h4 { color: var(--text-primary) !important; }

section[data-testid="stMain"] :focus-visible {
    outline: 2px solid var(--indigo) !important;
    outline-offset: 2px;
}


/* ---------- TOP BAR ---------- */

.topbar {
    display: flex; align-items: center; justify-content: space-between;
    gap: 1rem; padding: 1.1rem 1.6rem;
    border-radius: var(--radius-xl);
    background: var(--card); border: 1px solid var(--border);
    box-shadow: var(--shadow-card); margin-bottom: 1.4rem;
}

.topbar-left { display: flex; align-items: center; gap: 0.9rem; }

.topbar-icon {
    width: 46px; height: 46px; min-width: 46px;
    border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.5rem;
    background: linear-gradient(135deg, var(--indigo) 0%, #8f7bf5 100%);
    box-shadow: 0 6px 16px -6px rgba(91,91,240,0.55);
}

section[data-testid="stMain"] .topbar-title {
    color: var(--text-primary) !important;
    font-size: 1.35rem; font-weight: 800; letter-spacing: -0.01em; margin: 0;
}

section[data-testid="stMain"] .topbar-subtitle {
    color: var(--text-muted) !important;
    font-size: 0.86rem; margin: 0.1rem 0 0 0;
}

.status-chip {
    display: inline-flex; align-items: center; gap: 0.4rem;
    padding: 0.4rem 0.85rem; border-radius: 999px;
    font-size: 0.8rem; font-weight: 700; white-space: nowrap;
}
.status-chip.online  { background: var(--emerald-soft); color: var(--emerald) !important; }
.status-chip.offline { background: var(--amber-soft);   color: var(--amber)   !important; }
.status-dot { width: 7px; height: 7px; border-radius: 50%; background: currentColor; }


/* ---------- FEATURE PILLS ---------- */

.pill-row { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1.5rem; }

.pill {
    display: inline-flex; align-items: center; gap: 0.35rem;
    padding: 0.32rem 0.78rem; border-radius: 999px;
    font-size: 0.78rem; font-weight: 700;
    border: 1px solid var(--border); background: var(--card);
    color: var(--text-secondary) !important;
}


/* ---------- SECTION CARD ---------- */

.section-card {
    padding: 1.3rem 1.5rem; border-radius: var(--radius-lg);
    background: var(--card); border: 1px solid var(--border);
    box-shadow: var(--shadow-card); margin-bottom: 1rem;
}

.section-eyebrow {
    display: flex; align-items: center; gap: 0.5rem;
    font-size: 0.72rem; font-weight: 800; letter-spacing: 0.06em;
    text-transform: uppercase; color: var(--indigo) !important;
    margin-bottom: 0.3rem;
}

.section-title { font-size: 1.08rem; font-weight: 800; color: var(--text-primary) !important; margin-bottom: 0.15rem; }
.section-subtitle { font-size: 0.87rem; color: var(--text-muted) !important; margin: 0; }

.selected-file {
    display: inline-flex; align-items: center; gap: 0.4rem;
    padding: 0.55rem 0.9rem; margin: 0.7rem 0;
    border-radius: var(--radius-md);
    background: var(--emerald-soft); border: 1px solid #bdf0dd;
    color: var(--emerald) !important;
    font-size: 0.87rem; font-weight: 600; word-break: break-all;
}


/* ---------- EMPTY STATE ---------- */

.empty-state {
    text-align: center; padding: 1.6rem 1rem;
    color: var(--text-muted) !important; font-size: 0.92rem;
    background: var(--canvas); border: 1.5px dashed var(--border);
    border-radius: var(--radius-lg); margin-bottom: 1rem;
}


/* ---------- STAT CARDS ---------- */

.stat-card {
    display: flex; align-items: center; gap: 0.85rem;
    padding: 1rem 1.1rem; border-radius: var(--radius-lg);
    background: var(--card); border: 1px solid var(--border);
    box-shadow: var(--shadow-card); min-height: 78px;
}

.stat-icon {
    width: 42px; height: 42px; min-width: 42px; border-radius: 12px;
    display: flex; align-items: center; justify-content: center; font-size: 1.2rem;
}
.stat-icon.indigo  { background: var(--indigo-soft); }
.stat-icon.emerald { background: var(--emerald-soft); }
.stat-icon.amber   { background: var(--amber-soft); }
.stat-icon.rose    { background: var(--rose-soft); }

.stat-value { font-size: 1.3rem; font-weight: 800; color: var(--text-primary) !important; line-height: 1.1; word-break: break-word; }
.stat-label { font-size: 0.74rem; color: var(--text-muted) !important; text-transform: uppercase; letter-spacing: 0.04em; margin-top: 0.1rem; }


/* ---------- ARCHITECTURE (sidebar) ---------- */

.arch-step {
    display: flex; align-items: center; gap: 0.6rem;
    padding: 0.5rem 0.7rem; border-radius: 10px;
    background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.10);
    margin-bottom: 0.3rem; font-size: 0.84rem; font-weight: 600;
}

.arch-step .step-num {
    display: inline-flex; align-items: center; justify-content: center;
    width: 20px; height: 20px; min-width: 20px; border-radius: 6px;
    background: var(--indigo); color: white;
    font-size: 0.7rem; font-weight: 800;
}

.arch-arrow { text-align: center; color: #5a5f78 !important; font-size: 0.85rem; margin: -0.1rem 0 0.2rem 0; }


/* ---------- ANSWER ---------- */

.st-key-answer-card {
    padding: 1.3rem 1.6rem; border-radius: var(--radius-lg);
    background: linear-gradient(180deg, var(--indigo-soft) 0%, var(--card) 65%);
    border: 1px solid var(--border); box-shadow: var(--shadow-card);
    margin-bottom: 0.9rem;
}

.answer-heading {
    font-size: 0.95rem; font-weight: 800; color: var(--indigo) !important;
    display: flex; align-items: center; gap: 0.45rem; margin-bottom: 0.6rem;
}
.answer-question { font-size: 0.85rem; color: var(--text-muted) !important; margin: 0 0 0.6rem 0; }
.response-time { font-weight: 600; color: var(--text-muted) !important; font-size: 0.78rem; }


/* ---------- SOURCES ---------- */

.sources-title {
    display: flex; align-items: center; gap: 0.5rem;
    font-size: 1.05rem; font-weight: 800; color: var(--text-primary) !important;
    margin-top: 22px; margin-bottom: 12px;
}

.source-card {
    padding: 0.9rem 1.1rem; border-radius: var(--radius-md);
    border: 1px solid var(--border); border-left: 4px solid var(--indigo);
    background: var(--card); box-shadow: var(--shadow-card); margin-bottom: 0.6rem;
}

.source-title { font-weight: 700; color: var(--text-primary) !important; font-size: 0.9rem; margin-bottom: 0.35rem; }

.source-meta {
    display: flex; flex-wrap: wrap; gap: 0.8rem; align-items: center;
    font-size: 0.82rem; color: var(--text-secondary) !important;
}


/* ---------- RERANKER SCORES ---------- */

.score-badge { display: inline-block; padding: 0.12rem 0.6rem; border-radius: 999px; font-size: 0.75rem; font-weight: 800; }
.score-positive { background: var(--emerald-soft); color: var(--emerald) !important; }
.score-negative { background: var(--danger-soft);  color: var(--danger)  !important; }
.score-unknown  { background: var(--canvas); color: var(--text-muted) !important; }


/* ---------- SIDEBAR ---------- */

section[data-testid="stSidebar"] {
    background: #13141d !important;
    border-right: 1px solid rgba(255,255,255,0.08) !important;
}
section[data-testid="stSidebar"] > div:first-child { background: #13141d !important; }

section[data-testid="stSidebar"],
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] h4 { color: #e7e8f2 !important; }

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #ffffff !important; }

section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.10) !important; }

section[data-testid="stSidebar"] .stButton > button {
    width: 100% !important; min-height: 44px !important;
    background: #292a35 !important; color: #ffffff !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    border-radius: 12px !important; font-weight: 700 !important;
}
section[data-testid="stSidebar"] .stButton > button p,
section[data-testid="stSidebar"] .stButton > button span { color: #ffffff !important; }
section[data-testid="stSidebar"] .stButton > button:hover {
    background: #373846 !important; border-color: rgba(255,255,255,0.18) !important;
}

section[data-testid="stSidebar"] div[data-testid="stAlert"] {
    background: #242938 !important; border: 1px solid rgba(255,255,255,0.08) !important; color: #e7e8f2 !important;
}
section[data-testid="stSidebar"] div[data-testid="stAlert"] p,
section[data-testid="stSidebar"] div[data-testid="stAlert"] span,
section[data-testid="stSidebar"] div[data-testid="stAlert"] div { color: #e7e8f2 !important; }
section[data-testid="stSidebar"] div[data-testid="stAlert"] svg { color: #e7e8f2 !important; fill: currentColor !important; }

section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p,
section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] li { color: #d9dbea !important; }

section[data-testid="stSidebar"] code {
    color: #ffffff !important; background: #292a35 !important;
    border-radius: 6px !important; padding: 2px 6px !important;
}

section[data-testid="stSidebar"] .arch-step {
    color: #e7e8f2 !important;
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
}
section[data-testid="stSidebar"] .arch-step * { color: #e7e8f2 !important; }
section[data-testid="stSidebar"] .arch-step .step-num { color: #ffffff !important; }
section[data-testid="stSidebar"] .arch-arrow { color: #aeb2c7 !important; }


/* ---------- INPUTS / BUTTONS ---------- */

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

.stButton button,
div[data-testid="stFormSubmitButton"] button {
    border-radius: var(--radius-md) !important;
    font-weight: 800 !important;
    padding: 0.62rem 1.3rem !important;
    border: none !important;
}

div[data-testid="stButton"] button[kind="primary"],
div[data-testid="stFormSubmitButton"] button[kind="primary"] {
    background: linear-gradient(135deg, var(--indigo) 0%, #8f7bf5 100%) !important;
    box-shadow: 0 6px 16px -6px rgba(91,91,240,0.55) !important;
    color: #ffffff !important;
}

/* Forms: no extra frame, the cards provide the structure */
div[data-testid="stForm"] { border: none !important; padding: 0 !important; background: transparent !important; }

/* Login card */
.st-key-login-card div[data-testid="stForm"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-xl) !important;
    box-shadow: var(--shadow-card);
    padding: 1.6rem 1.8rem !important;
}


/* ---------- FILE UPLOADER ---------- */

div[data-testid="stFileUploader"] { margin-bottom: 0.5rem; }

div[data-testid="stFileUploaderDropzone"] {
    border-radius: var(--radius-md) !important;
    border: 1.5px dashed #c7cae8 !important;
    background: #fafaff !important;
    color: var(--text-primary) !important;
}
div[data-testid="stFileUploaderDropzone"] * { color: var(--text-primary) !important; }
div[data-testid="stFileUploaderDropzone"] button {
    color: var(--text-primary) !important;
    background: #ffffff !important;
    border: 1px solid var(--border) !important;
}


/* ---------- ALERTS / EXPANDER ---------- */

div[data-testid="stAlert"] { color: var(--text-primary) !important; border-radius: var(--radius-md) !important; }

section[data-testid="stMain"] div[data-testid="stExpander"],
section[data-testid="stMain"] div[data-testid="stExpander"] p { color: var(--text-primary) !important; }

section[data-testid="stMain"] div[data-testid="stExpander"] {
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--border) !important;
    box-shadow: var(--shadow-card);
    background: var(--card);
}


/* ---------- RESPONSIVE ---------- */

@media (max-width: 760px) {
    .topbar { flex-direction: column; align-items: flex-start; }
    .block-container { padding-left: 1rem; padding-right: 1rem; }
}


/* ---------- SIDEBAR TOGGLE ---------- */

div[data-testid="collapsedControl"] {
    visibility: visible !important; opacity: 1 !important;
    display: block !important; pointer-events: auto !important;
    z-index: 2147483647 !important;
}

div[data-testid="collapsedControl"] button,
div[data-testid="collapsedControl"] button[data-testid="baseButton-headerNoPadding"] {
    visibility: visible !important; opacity: 1 !important; pointer-events: auto !important;

    width: 44px !important; height: 44px !important;
    min-width: 44px !important; min-height: 44px !important;

    display: flex !important; align-items: center !important; justify-content: center !important;

    padding: 0 !important; margin: 4px !important;

    background-color: #ffffff !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
    background-size: 25px 25px !important;

    /* Purple double-chevron drawn directly into the button. */
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='28' height='28' viewBox='0 0 28 28'%3E%3Cpath d='M7 5l7 9-7 9M14 5l7 9-7 9' fill='none' stroke='%234338ca' stroke-width='2.8' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E") !important;

    border: 1px solid #c7cbea !important;
    border-radius: 12px !important;
    box-shadow: 0 3px 12px rgba(23,25,35,0.16) !important;

    color: #4338ca !important;
    -webkit-text-fill-color: #4338ca !important;
}

div[data-testid="collapsedControl"] button:hover,
div[data-testid="collapsedControl"] button[data-testid="baseButton-headerNoPadding"]:hover {
    background-color: #f0f1ff !important;
    border-color: #aeb4e8 !important;
}

/* Hide Streamlit's own icon so it cannot overlay the replacement icon. */
div[data-testid="collapsedControl"] button > *,
div[data-testid="collapsedControl"] button svg,
div[data-testid="collapsedControl"] button span,
div[data-testid="collapsedControl"] button i {
    visibility: hidden !important; opacity: 0 !important;
}

div[data-testid="collapsedControl"] button::before,
div[data-testid="collapsedControl"] button::after {
    content: "" !important; display: none !important;
}

header[data-testid="stHeader"] { z-index: 2147483646 !important; }

header[data-testid="stHeader"] div[data-testid="collapsedControl"] {
    z-index: 2147483647 !important;
    visibility: visible !important; opacity: 1 !important; pointer-events: auto !important;
}

</style>
"""

# Injected first so the login screen is styled too.
st.markdown(CSS, unsafe_allow_html=True)


# ============================================================
# HELPERS
# ============================================================

def reset_auth(notice: str | None = None) -> None:
    """Clear everything tied to the signed-in user."""
    st.session_state.access_token = None
    st.session_state.username = None
    st.session_state.user_role = None
    st.session_state.history = []
    st.session_state.last_result = None
    st.session_state.auth_notice = notice


def is_auth_error(error: Exception) -> bool:
    text = str(error).lower()
    return any(token in text for token in ("401", "unauthorized", "token expired", "invalid token"))


def score_class(score) -> str:
    # Cross-encoder scores are raw relevance scores, not probabilities.
    if score is None:
        return "score-unknown"
    return "score-positive" if score >= 0 else "score-negative"


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ============================================================
# AUTHENTICATION
# ============================================================

def login_user(username: str, password: str) -> bool:
    """Authenticate the user through the FastAPI backend."""

    try:
        result = api_client.login(username=username, password=password)

        st.session_state.access_token = result["access_token"]
        st.session_state.username = username
        st.session_state.user_role = result.get("role")
        st.session_state.auth_notice = None
        return True

    except Exception as exc:
        st.error(f"Login failed: {exc}")
        return False


# ============================================================
# LOGIN SCREEN
# ============================================================

if not st.session_state.access_token:

    _, center, _ = st.columns([1, 1.4, 1])

    with center:
        st.markdown(
            """
            <div style="text-align:center; padding:40px 0 20px 0;">
                <div class="topbar-icon" style="margin:0 auto 14px auto; width:56px; height:56px; font-size:1.8rem;">🔐</div>
                <h1 style="margin:0;">Enterprise Knowledge Base</h1>
                <p style="font-size:16px; color:#8b90a8;">
                    Secure AI-powered Knowledge Retrieval System
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.session_state.auth_notice:
            st.warning(st.session_state.auth_notice)

        with st.container(key="login-card"):
            with st.form("login_form"):

                st.subheader("Sign in")

                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")

                submitted = st.form_submit_button("Login", type="primary", use_container_width=True)

                if submitted:
                    if not username.strip() or not password:
                        st.error("Please enter both username and password.")
                    else:
                        with st.spinner("Signing in..."):
                            ok = login_user(username.strip(), password)
                        if ok:
                            st.rerun()

    st.stop()


# ===========================================================
# RAG SERVICE LOADER
# ===========================================================

@st.cache_resource(show_spinner=False, max_entries=2)
def load_rag_service(pdf_path: str, file_version: int):
    """
    Build a RAG service for the selected PDF.
    file_version forces a rebuild if a same-named file is replaced.
    """

    loader = PDFLoader()
    documents = loader.load(pdf_path)

    if not documents:
        raise ValueError("The PDF contains no extractable text.")

    chunker = TextChunker(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = chunker.chunk_documents(documents)

    if not chunks:
        raise ValueError("No chunks were generated from the PDF.")

    rag_service = RAGService(chunks)
    return rag_service, len(chunks)


def clear_local_document() -> None:
    st.session_state.active_pdf_path = None
    st.session_state.indexed_document_name = None
    st.session_state.pdf_file_version = None
    st.session_state.history = []
    st.session_state.last_result = None
    load_rag_service.clear()


# ===========================================================
# TOP BAR
# ===========================================================

# The FastAPI server knowledge base is available after login.
# A local PDF is optional and is used for the local processing flow.
is_online = bool(st.session_state.access_token)
status_class = "online" if is_online else "offline"
status_label = "Knowledge Base Online" if is_online else "Awaiting Login"

st.markdown(
    f"""
<div class="topbar">
<div class="topbar-left">
<div class="topbar-icon">🧠</div>
<div>
<p class="topbar-title">Enterprise Knowledge Base</p>
<p class="topbar-subtitle">Hybrid retrieval &middot; cross-encoder reranking &middot; grounded answers with {esc(MODEL)}</p>
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
<span class="pill">🤖 {esc(MODEL)}</span>
<span class="pill">✅ Grounded Answers</span>
</div>
""",
    unsafe_allow_html=True,
)


# ===========================================================
# PDF UPLOAD SECTION
# ===========================================================

st.markdown(
    f"""
<div class="section-card">
<div class="section-eyebrow">📥 Step 1</div>
<div class="section-title">Add Document to Knowledge Base</div>
<p class="section-subtitle">Upload a PDF (up to {MAX_UPLOAD_MB} MB), index it, then ask questions about its contents.</p>
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

    # Strip any path and unsafe characters from the client-supplied name.
    safe_filename = re.sub(r"[^A-Za-z0-9._ -]", "_", Path(uploaded_file.name).name) or "document.pdf"

    st.markdown(
        f"""<div class="selected-file">📄 {esc(safe_filename)}</div>""",
        unsafe_allow_html=True,
    )

    too_large = uploaded_file.size > MAX_UPLOAD_MB * 1024 * 1024
    if too_large:
        st.error(f"This file is larger than {MAX_UPLOAD_MB} MB.")

    do_index = st.button("🚀 Index PDF", type="primary", disabled=too_large)

    if do_index:
        try:
            destination = UPLOAD_DIR / safe_filename

            with open(destination, "wb") as file:
                file.write(uploaded_file.getbuffer())

            file_version = destination.stat().st_mtime_ns

            # Load once here (result is cached), so errors surface at click time
            # and the page never re-runs a failing load on every interaction.
            with st.spinner("Reading, chunking and indexing the PDF..."):
                load_rag_service(str(destination), file_version)

            st.session_state.active_pdf_path = str(destination)
            st.session_state.indexed_document_name = safe_filename
            st.session_state.pdf_file_version = file_version
            st.session_state.history = []
            st.session_state.last_result = None
            st.session_state.index_success_message = f"Successfully indexed '{safe_filename}'."

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

chunk_count = 0
rag_service = None

if active_pdf_path is None:

    st.markdown(
        """
<div class="empty-state">
📚 No local PDF is currently indexed.<br>Upload a PDF above to process a document locally, or query the server knowledge base directly.
</div>
""",
        unsafe_allow_html=True,
    )

else:
    active_path = Path(active_pdf_path)

    if not active_path.exists():
        clear_local_document()
        st.rerun()

    file_version = st.session_state.get("pdf_file_version") or active_path.stat().st_mtime_ns

    try:
        with st.spinner("Preparing the knowledge base..."):
            rag_service, chunk_count = load_rag_service(str(active_path), file_version)
    except Exception as error:
        st.error(f"Unable to load the indexed document: {error}")
        clear_local_document()
        active_pdf_path = None
        active_document_name = None


# ===========================================================
# STAT CARDS
# ===========================================================

def stat_card(icon: str, tone: str, value, label: str, small: bool = False) -> str:
    size = ' style="font-size:0.98rem;"' if small else ""
    return f"""
<div class="stat-card">
<div class="stat-icon {tone}">{icon}</div>
<div><div class="stat-value"{size}>{esc(value)}</div><div class="stat-label">{label}</div></div>
</div>
"""


m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(stat_card("🧩", "indigo", chunk_count, "Knowledge Chunks"), unsafe_allow_html=True)

with m2:
    st.markdown(stat_card("📄", "emerald", 1 if active_pdf_path else 0, "Documents"), unsafe_allow_html=True)

with m3:
    st.markdown(stat_card("🤖", "amber", MODEL, "LLM", small=True), unsafe_allow_html=True)

with m4:
    questions_metric = st.empty()
    questions_metric.markdown(
        stat_card("💬", "rose", len(st.session_state.history), "Questions Asked"),
        unsafe_allow_html=True,
    )

st.write("")


# ===========================================================
# SIDEBAR — nav rail
# ===========================================================

with st.sidebar:

    st.header("👤 Account")

    if st.session_state.username:
        st.markdown(f"**User:** `{st.session_state.username}`")

    if st.session_state.user_role:
        st.markdown(f"**Role:** `{st.session_state.user_role}`")

    if st.button("🚪 Logout", use_container_width=True):
        reset_auth()
        st.rerun()

    st.divider()

    st.header("📚 Knowledge Base")

    if active_pdf_path:
        st.success("Knowledge Base Online")
        st.divider()
        st.markdown("**Current Document**")
        st.markdown(f"📄 `{active_document_name}`")
        st.markdown("**Knowledge Chunks**")
        st.markdown(f"`{chunk_count}`")

        if st.button("🗑️ Clear Knowledge Base", use_container_width=True):
            clear_local_document()
            st.rerun()

    else:
        st.info("Using the server knowledge base.")
        st.markdown("You can upload and index a PDF above for local document processing.")

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
            f"""<div class="arch-step"><span class="step-num">{i + 1}</span>{esc(step)}</div>""",
            unsafe_allow_html=True,
        )
        if i != len(steps) - 1:
            st.markdown('<div class="arch-arrow">↓</div>', unsafe_allow_html=True)

    if st.session_state.history:
        st.divider()
        st.header("🕘 Recent Questions")

        for past_q in reversed(st.session_state.history[-5:]):
            st.markdown(f"- {esc(past_q)}")

        if st.button("🧹 Clear History", use_container_width=True):
            st.session_state.history = []
            st.session_state.last_result = None
            st.rerun()


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

# A form lets the Enter key submit the question, not just the button.
with st.form("query_form", clear_on_submit=False):
    col_input, col_button = st.columns([5, 1])

    with col_input:
        query = st.text_input(
            "Enter your question",
            placeholder="e.g. What is the leave policy?",
            label_visibility="collapsed",
        )

    with col_button:
        ask_button = st.form_submit_button("🔍 Ask", type="primary", use_container_width=True)

    website_url = st.text_input(
            "Website URL (optional)",
            placeholder="e.g. https://example.com",
        )

# ===========================================================
# ANSWER GENERATION
# ===========================================================

if ask_button:

    clean_query = query.strip()

    if not clean_query:
        st.warning("Please enter a question.")

    else:
        with st.spinner("Searching knowledge base..."):
            try:
                start = time.perf_counter()

                result = api_client.query(
                    token=st.session_state.access_token,
                    query=clean_query,
                    url=website_url.strip() or None,
                )

                elapsed = time.perf_counter() - start

                st.session_state.history.append(clean_query)
                st.session_state.last_result = {
                    "question": clean_query,
                    "answer": result.get("answer", ""),
                    "sources": result.get("sources", []) or [],
                    "elapsed": elapsed,
                    "document": active_document_name,
                }

                questions_metric.markdown(
                    stat_card("💬", "rose", len(st.session_state.history), "Questions Asked"),
                    unsafe_allow_html=True,
                )

            except Exception as error:
                error_message = str(error)

                if isinstance(error, RuntimeError):
                    st.error(f"⚠️ **Request error**\n\n{error}")

                if "403" in error_message or "Forbidden" in error_message:
                    st.error(
                        "🔒 **Access denied**\n\n"
                        "You don't have permission to access this information. "
                        "Please contact your administrator if you need access."
                    )
                elif is_auth_error(error):
                    reset_auth("Your session has expired. Please sign in again.")
                    st.rerun()
                else:
                    st.error(f"Unable to generate answer: {error}")                



# ===========================================================
# RESULT RENDERING (persists across reruns)
# ===========================================================

last_result = st.session_state.last_result

if last_result:

    st.divider()

    with st.container(key="answer-card"):
        st.markdown(
            f"""<div class="answer-heading">💡 <span>Answer</span>"""
            f"""<span class="response-time">({last_result["elapsed"]:.2f}s)</span></div>"""
            f"""<p class="answer-question">Q: {esc(last_result["question"])}</p>""",
            unsafe_allow_html=True,
        )
        st.markdown(last_result["answer"] or "_The knowledge base returned no answer._")

    st.markdown("""<div class="sources-title">📚 Sources</div>""", unsafe_allow_html=True)

    if not last_result["sources"]:
        st.info("No sources were returned for this answer.")

    for index, source in enumerate(last_result["sources"], start=1):
        score = to_float(source.get("rerank_score"))
        badge_class = score_class(score)
        score_text = f"{score:.4f}" if score is not None else "n/a"

        source_name = esc(source.get("source", "Unknown source"))
        page = esc(source.get("page", "Unknown"))
        chunk_id = esc(source.get("chunk_id", "Unknown"))

        st.markdown(
            f"""
<div class="source-card">
<div class="source-title">Source {index} — {source_name}</div>
<div class="source-meta">
<span>📑 Page {page}</span>
<span>🔗 Chunk {chunk_id}</span>
<span class="score-badge {badge_class}">🎯 {score_text}</span>
</div>
</div>
""",
            unsafe_allow_html=True,
        )

    with st.expander("🔎 How this answer was generated"):
        document_label = last_result["document"] or "Server knowledge base"

        st.markdown(
            f"""
**Current document:** `{document_label}`

**Pipeline**

1. Streamlit UI
2. FastAPI authentication / JWT
3. Redis cache lookup
4. LangGraph routing
5. Hybrid retrieval + reranking
6. Relevant evidence selection
7. {MODEL} generation
8. Guardrails / grounding validation
9. Answer + sources

**Response time:** `{last_result["elapsed"]:.2f} seconds`

**Evidence returned:** `{len(last_result["sources"])} sources`

**LLM:** `{MODEL}`

**Gateway:** `LiteLLM`
"""
        )

elif rag_service is None:
    st.info("💡 You can ask questions against the server knowledge base, or upload a PDF above for local processing.")
