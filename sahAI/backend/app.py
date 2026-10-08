import os
import re
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

if __package__:
    from .config import PROJECT_DIR, REGULATION_PDF_PATH
    from .ingest import extract_pages
    from .llm import AIServiceError, generate_answer
    from .rag import retrieve_passages
else:
    project_root = Path(__file__).resolve().parents[1]
    repo_root = project_root.parent
    for candidate in (repo_root, project_root):
        if str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))

    try:
        from sahAI.backend.config import PROJECT_DIR, REGULATION_PDF_PATH
        from sahAI.backend.ingest import extract_pages
        from sahAI.backend.llm import AIServiceError, generate_answer
        from sahAI.backend.rag import retrieve_passages
    except ModuleNotFoundError:
        from backend.config import PROJECT_DIR, REGULATION_PDF_PATH
        from backend.ingest import extract_pages
        from backend.llm import AIServiceError, generate_answer
        from backend.rag import retrieve_passages

def load_environment() -> None:
    for env_path in (
        Path(__file__).resolve().parents[2] / ".env",
        PROJECT_DIR / ".env",
    ):
        load_dotenv(env_path)


load_environment()

st.set_page_config(page_title="sahAI — R25 Assistant", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

    :root {
        --ink: #1d1d1f;
        --muted: #707076;
        --canvas: #f5f5f7;
        --surface: #ffffff;
        --line: #e4e4e8;
        --accent: #1671e8;
        --accent-soft: #edf4ff;
    }

    .stApp {
        background: var(--canvas);
        color: var(--ink);
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'DM Sans', sans-serif;
    }
    .stApp::before {
        content: "";
        position: fixed;
        inset: 0 0 auto;
        height: 2px;
        z-index: 1000;
        background: var(--accent);
    }
    [data-testid="stHeader"] { background: rgba(245, 245, 247, 0.86); }
    [data-testid="stMainBlockContainer"] {
        max-width: 1120px;
        padding: 1.5rem 2.6rem 8rem;
    }
    h1, h2, h3, p, label, button, textarea {
        color: var(--ink);
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'DM Sans', sans-serif;
    }
    h1 {
        font-size: 2.8rem !important;
        font-weight: 600 !important;
        line-height: 1.08 !important;
        margin: 0 !important;
    }
    [data-testid="stCaptionContainer"] {
        color: var(--muted);
        font-size: 0.8rem;
    }
    [data-testid="stSidebar"] {
        background: #f0f0f2;
        border-right: 1px solid #e1e1e5;
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0.72rem;
    }
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: var(--ink);
        font-size: 0.9rem;
        font-weight: 600;
    }
    [data-testid="stSidebar"] [data-testid="stAlert"] {
        border: 1px solid var(--line);
        border-radius: 8px;
        background: var(--surface);
        color: var(--ink);
    }
    [data-testid="stButton"] > button {
        min-height: 4rem;
        padding: 0.8rem 1.1rem;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: var(--surface);
        color: var(--ink);
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'DM Sans', sans-serif;
        font-size: 0.92rem;
        font-weight: 500;
        text-align: left;
        transition: border-color 160ms ease, background 160ms ease, transform 160ms ease;
        box-shadow: 0 1px 2px rgba(29, 29, 31, 0.035);
    }
    [data-testid="stButton"] > button:hover {
        border-color: #a7c8f3;
        background: var(--accent-soft);
        color: var(--ink);
        transform: translateY(-1px);
        box-shadow: 0 5px 16px rgba(29, 75, 130, 0.08);
    }
    [data-testid="stChatMessage"] {
        border: 1px solid var(--line);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.88);
        padding: 1rem 1.1rem;
        box-shadow: 0 2px 8px rgba(29, 29, 31, 0.025);
    }
    [data-testid="stChatMessageAvatar"] { display: none !important; }
    [data-testid="stChatMessage"] > div:first-child { display: none !important; }
    [data-testid="stChatInput"] textarea {
        border: 1px solid #d8d8dc;
        border-radius: 8px;
        background: var(--surface);
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'DM Sans', sans-serif;
        font-size: 0.96rem;
    }
    [data-testid="stChatInput"] textarea:focus {
        border-color: var(--accent);
        box-shadow: 0 0 0 3px rgba(22, 113, 232, 0.12);
    }
    [data-testid="stBottom"] {
        background: rgba(245, 245, 247, 0.9);
        border-top: 1px solid rgba(228, 228, 232, 0.8);
        backdrop-filter: blur(20px);
    }
    [data-testid="stBottom"] [data-testid="stBottomBlockContainer"] {
        max-width: 1040px;
        padding-top: 0.75rem;
        padding-bottom: 0.85rem;
    }
    [data-testid="stExpander"] {
        border: 1px solid var(--line);
        border-radius: 8px;
        background: var(--surface);
    }
    .masthead {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        padding-bottom: 1.15rem;
        border-bottom: 1px solid var(--line);
        margin-bottom: 2.2rem;
    }
    .brand-lockup {
        display: flex;
        align-items: center;
        gap: 0.65rem;
        color: var(--ink);
        font-size: 1rem;
        font-weight: 650;
    }
    .brand-mark {
        display: grid;
        width: 2rem;
        height: 2rem;
        place-items: center;
        border-radius: 7px;
        background: var(--ink);
        color: #fff;
        font-size: 1rem;
        font-weight: 600;
    }
    .edition-label, .hero-overline, .section-overline {
        color: var(--muted);
        font-size: 0.68rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    .hero-block {
        margin-bottom: 2.35rem;
        animation: arrive 420ms ease-out both;
    }
    .hero-block h1 {
        margin: 0.45rem 0 0.55rem !important;
        letter-spacing: -0.035em;
    }
    .hero-subtitle {
        color: var(--muted);
        font-size: 0.96rem;
    }
    .section-heading {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 1rem;
        margin: 0 0 0.9rem;
    }
    .section-heading h2 {
        margin: 0;
        font-size: 1.05rem;
        font-weight: 600;
    }
    .sidebar-source {
        padding: 0.2rem 0 0.4rem;
    }
    .sidebar-source-label {
        color: var(--muted);
        font-size: 0.66rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    .sidebar-source-state {
        margin-top: 0.45rem;
        color: var(--ink);
        font-size: 1rem;
        font-weight: 600;
    }
    .sidebar-source-detail {
        margin-top: 0.3rem;
        color: var(--muted);
        font-size: 0.76rem;
        line-height: 1.5;
        overflow-wrap: anywhere;
    }
    @keyframes arrive {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    hr { border-color: var(--line); }
    @media (max-width: 700px) {
        [data-testid="stMainBlockContainer"] {
            padding: 1.1rem 1rem 7rem;
        }
        .masthead { margin-bottom: 1.65rem; }
        .hero-block { margin-bottom: 1.7rem; }
        .hero-block h1 { font-size: 2.25rem !important; }
        .edition-label { font-size: 0.6rem; text-align: right; }
        [data-testid="stBottom"] [data-testid="stBottomBlockContainer"] {
            padding-left: 0.8rem;
            padding-right: 0.8rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

SUGGESTED_QUESTIONS = [
    "What attendance is required for semester-end exams?",
    "How are internal and semester-end marks divided?",
    "How many credits are required to graduate?",
    "How are SGPA and CGPA calculated?",
]

SMALL_TALK_PATTERNS = {
    "greeting": [
        "hi", "hello", "hey", "good morning", "good evening", "good afternoon",
        "greetings", "yo"
    ],
    "farewell": [
        "bye", "goodbye", "see you", "talk later", "later", "thanks", "thank you"
    ],
}


def get_small_talk_response(question: str) -> str | None:
    if not question or not question.strip():
        return None

    normalized = re.sub(r"[^a-z0-9\s]", " ", question.lower())
    normalized = " ".join(normalized.split())

    if any(token in normalized for token in SMALL_TALK_PATTERNS["greeting"]):
        return (
            "Hi! I’m sahAI, your MLRS-BT25 / R25 regulation assistant. Ask me about "
            "attendance, credits, exams, grading, or any specific academic rule."
        )

    if any(token in normalized for token in SMALL_TALK_PATTERNS["farewell"]):
        return (
            "Goodbye! If you want, ask me about the R25 regulations for attendance, exams, "
            "credits, grading, or academic rules."
        )

    return None


@st.cache_data(show_spinner=False)
def load_regulation(pdf_path: str, modified_ns: int):
    del modified_ns  # Included in the cache key so replacing the PDF refreshes it.
    return extract_pages(pdf_path)


def render_citations(citations: list[dict]):
    if not citations:
        st.caption("No supporting passage was found in the R25 document.")
        return

    st.markdown("**Supporting passages**")
    for citation in citations:
        regulation_page = citation["regulation_page"]
        page_label = f"PDF p. {citation['pdf_page']}"
        if regulation_page is not None:
            page_label += f" / Regulation p. {regulation_page}"
        with st.expander(f"{citation['section']} — {page_label}"):
            st.write(citation["excerpt"])


if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown(
    """
    <div class="masthead">
        <div class="brand-lockup"><span class="brand-mark">s</span><span>sahAI</span></div>
        <div class="edition-label">MLRITM / R25 / CSM</div>
    </div>
    <div class="hero-block">
        <div class="hero-overline">Regulation desk</div>
        <h1>R25, made clear.</h1>
        <div class="hero-subtitle">Academic regulations for MLRITM CSM</div>
    </div>
    """,
    unsafe_allow_html=True,
)

pages = []
source_error = None
if REGULATION_PDF_PATH.is_file():
    try:
        file_stat = REGULATION_PDF_PATH.stat()
        pages = load_regulation(str(REGULATION_PDF_PATH), file_stat.st_mtime_ns)
    except Exception:
        source_error = (
            "The R25 PDF could not be read. Check that it is a text-searchable PDF "
            "and try replacing the local copy."
        )

with st.sidebar:
    st.markdown('<div class="sidebar-source-label">Reference library</div>', unsafe_allow_html=True)
    st.subheader("R25 regulations")
    if pages:
        st.markdown(
            f'<div class="sidebar-source"><div class="sidebar-source-state">Source ready</div>'
            f'<div class="sidebar-source-detail">{len(pages)} pages<br>{REGULATION_PDF_PATH.name}</div></div>',
            unsafe_allow_html=True,
        )
    elif source_error:
        st.error(source_error)
    else:
        st.warning("R25 source not found")
        st.caption("Add the authorized PDF or set SAHAI_REGULATION_PDF.")

    st.divider()
    st.caption("Questions and cited passages are sent to Google Gemini. Guidance is not an official decision.")

if source_error:
    st.error(source_error)
elif not pages:
    st.info(
        "R25 regulations are unavailable. Add the authorized PDF to enable answers."
    )

if not st.session_state.messages:
    st.markdown(
        '<div class="section-heading"><h2>Start with a topic</h2>'
        '<span class="section-overline">Common questions</span></div>',
        unsafe_allow_html=True,
    )
    suggestion_columns = st.columns(2)
    for index, question in enumerate(SUGGESTED_QUESTIONS):
        with suggestion_columns[index % 2]:
            if st.button(question, key=f"suggested-question-{index}", use_container_width=True):
                st.session_state.pending_question = question
                st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message.get("is_error"):
            st.error(message["content"])
        else:
            st.markdown(message["content"])
            if message["role"] == "assistant":
                if message.get("status") == "not_found":
                    st.caption(
                        "This question may need a staff member’s guidance. "
                        "Check with your department before acting on it."
                    )
                render_citations(message.get("citations", []))

pending_question = st.session_state.pop("pending_question", None)
typed_question = st.chat_input("Ask about attendance, exams, credits, or grading")
question = pending_question or typed_question

if question:
    cleaned_question = question.strip()
    if len(cleaned_question) < 2:
        st.warning("Please enter a question with at least two characters.")
    else:
        st.session_state.messages.append(
            {"role": "user", "content": cleaned_question}
        )
        with st.chat_message("user"):
            st.markdown(cleaned_question)

        with st.chat_message("assistant"):
            small_talk_response = get_small_talk_response(cleaned_question)
            if small_talk_response:
                st.markdown(small_talk_response)
                st.session_state.messages.append(
                    {"role": "assistant", "content": small_talk_response, "status": "answered"}
                )
            elif not pages:
                error_message = (
                    "The R25 regulation source is not available. Add the private "
                    "PDF locally, then try again."
                )
                st.error(error_message)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_message, "is_error": True}
                )
            else:
                with st.spinner("Checking the R25 regulation…"):
                    try:
                        passages = retrieve_passages(cleaned_question, pages)
                        if not passages:
                            response = {
                                "answer": (
                                    "I couldn’t find a relevant passage in the "
                                    "R25 regulation. Try rephrasing the question "
                                    "or check with your department."
                                ),
                                "status": "not_found",
                                "citations": [],
                                "needs_human_review": True,
                            }
                        else:
                            response = generate_answer(cleaned_question, passages)

                        st.markdown(response["answer"])
                        if response["status"] == "not_found":
                            st.caption(
                                "This question may need a staff member’s guidance. "
                                "Check with your department before acting on it."
                            )
                        render_citations(response["citations"])
                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": response["answer"],
                                "status": response["status"],
                                "citations": response["citations"],
                            }
                        )
                    except AIServiceError as error:
                        st.error(str(error))
                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": str(error),
                                "is_error": True,
                            }
                        )
