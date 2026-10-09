import base64
import logging
import os
import re
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

if __package__:
    from .config import PROJECT_DIR, REGULATION_PDF_PATH
    from .ingest import extract_pages
    from .llm import AIServiceError, generate_answer, generate_general_answer
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
        from sahAI.backend.llm import AIServiceError, generate_answer, generate_general_answer
        from sahAI.backend.rag import retrieve_passages
    except ModuleNotFoundError:
        from backend.config import PROJECT_DIR, REGULATION_PDF_PATH
        from backend.ingest import extract_pages
        from backend.llm import AIServiceError, generate_answer, generate_general_answer
        from backend.rag import retrieve_passages

def load_environment() -> None:
    for env_path in (
        Path(__file__).resolve().parents[2] / ".env",
        PROJECT_DIR / ".env",
    ):
        load_dotenv(env_path)


load_environment()
logger = logging.getLogger(__name__)

st.set_page_config(page_title="sahAI — R25 Assistant", layout="wide")

logo_path = PROJECT_DIR / "logo.png"
logo_data = base64.b64encode(logo_path.read_bytes()).decode("ascii") if logo_path.is_file() else ""

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

    :root {
        --ink: #f1f8f3;
        --muted: #a1b5a8;
        --canvas: #07120d;
        --surface: #102219;
        --line: #284638;
        --accent: #c5f44a;
        --accent-soft: #183522;
    }

    .stApp {
        background:
            radial-gradient(ellipse at 50% -18%, rgba(23, 107, 68, 0.35), transparent 48%),
            radial-gradient(ellipse at 100% 65%, rgba(148, 196, 53, 0.08), transparent 34%),
            var(--canvas);
        color: var(--ink);
        font-family: 'Manrope', sans-serif;
    }
    .stApp::before {
        content: "";
        position: fixed;
        inset: 0 0 auto;
        height: 2px;
        z-index: 1000;
        background: linear-gradient(90deg, #21dc91, #c5f44a);
    }
    [data-testid="stHeader"] {
        background: transparent !important;
        box-shadow: none !important;
    }
    [data-testid="stToolbar"] { background: transparent !important; }
    [data-testid="stMainBlockContainer"] {
        max-width: 1060px;
        padding: 1.2rem 2.6rem 8rem;
    }
    h1, h2, h3, p, label, button, textarea {
        color: var(--ink);
        font-family: 'Manrope', sans-serif;
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
        background: rgba(9, 24, 16, 0.92);
        border-right: 1px solid var(--line);
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
        font-family: 'Manrope', sans-serif;
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
        background: linear-gradient(135deg, rgba(17, 37, 26, 0.96), rgba(12, 29, 20, 0.94));
        padding: 1rem 1.1rem;
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.14);
    }
    [data-testid="stChatMessageAvatar"] { display: none !important; }
    [data-testid="stChatInput"] textarea {
        border: 1px solid #355844;
        border-radius: 8px;
        background: #0d1e14;
        color: var(--ink);
        font-family: 'Manrope', sans-serif;
        font-size: 0.96rem;
    }
    [data-testid="stChatInput"] textarea:focus {
        border-color: var(--accent);
        box-shadow: 0 0 0 3px rgba(197, 244, 74, 0.14);
    }
    [data-testid="stBottom"] {
        background: rgba(7, 18, 13, 0.88);
        border-top: 1px solid rgba(40, 70, 56, 0.9);
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
    [data-testid="stExpander"] summary,
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li { color: var(--ink); }
    [data-testid="stAlert"] {
        border-radius: 8px;
        background: #12271b;
        color: var(--ink);
    }
    [data-testid="stChatInput"] button {
        background: var(--accent) !important;
        color: #102017 !important;
        border: 0 !important;
    }
    .masthead {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        padding: 0.45rem 0 1.1rem;
        border-bottom: 1px solid var(--line);
        margin-bottom: 1.8rem;
    }
    .brand-lockup {
        display: flex;
        align-items: center;
        gap: 0.85rem;
        color: var(--ink);
        font-size: 1.2rem;
        font-weight: 800;
    }
    .brand-logo {
        width: 5.5rem;
        height: 5.5rem;
        object-fit: contain;
        filter: drop-shadow(0 0 18px rgba(41, 231, 143, 0.25));
    }
    .brand-name small {
        display: block;
        margin-top: 0.08rem;
        color: var(--muted);
        font-size: 0.66rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .edition-label, .hero-overline, .section-overline {
        color: #c5f44a;
        font-size: 0.68rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    .hero-block {
        margin-bottom: 2.35rem;
        animation: arrive 420ms ease-out both;
    }
    .hero-block h1 { color: #f2faef; }
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
        .masthead { margin-bottom: 1.4rem; }
        .brand-logo { width: 4.2rem; height: 4.2rem; }
        .brand-lockup { font-size: 1rem; gap: 0.55rem; }
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
REGULATION_CUES = (
    "r25", "r 25", "bt25", "mlritm", "regulation", "attendance",
    "semester end", "semester-end", "exam", "examination", "internal marks",
    "external marks", "sgpa", "cgpa", "credits", "marks", "backlog",
    "supplementary", "detained", "revaluation", "promotion", "credit requirement",
)


def get_small_talk_response(question: str) -> str | None:
    if not question or not question.strip():
        return None

    normalized = re.sub(r"[^a-z0-9\s]", " ", question.lower())
    normalized = " ".join(normalized.split())

    greetings = SMALL_TALK_PATTERNS["greeting"]
    if normalized in greetings or normalized in {f"{greeting} there" for greeting in greetings}:
        return (
            "Hi! I’m sahAI, your MLRS-BT25 / R25 regulation assistant. Ask me about "
            "attendance, credits, exams, grading, or any specific academic rule."
        )

    if normalized in SMALL_TALK_PATTERNS["farewell"]:
        return (
            "Goodbye! If you want, ask me about the R25 regulations for attendance, exams, "
            "credits, grading, or academic rules."
        )

    return None


def is_regulation_question(question: str) -> bool:
    normalized = re.sub(r"[^a-z0-9\s]", " ", question.lower())
    normalized = " ".join(normalized.split())
    return any(cue in normalized for cue in REGULATION_CUES)


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
    f"""
    <div class="masthead">
        <div class="brand-lockup"><img class="brand-logo" src="data:image/png;base64,{logo_data}" alt="sahAI logo"><span class="brand-name">R25 Student Desk<small>MLRITM Academic Guide</small></span></div>
        <div class="edition-label">MLRITM / R25 / CSM</div>
    </div>
    <div class="hero-block">
        <div class="hero-overline">Student desk</div>
        <h1>R25, made clear.</h1>
        <div class="hero-subtitle">R25 answers, study topics, and general questions</div>
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
        "R25 answers need the regulation PDF. General questions are still available."
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
            if message["role"] == "assistant" and message.get("answer_type") == "general":
                st.caption("General knowledge, not verified against the R25 regulations.")
            elif message["role"] == "assistant" and message.get("answer_type") != "small_talk":
                if message.get("answer_type") == "regulation_fallback":
                    st.caption("AI summary unavailable. Showing matching R25 source text.")
                elif message.get("status") == "not_found":
                    st.caption(
                        "This question may need a staff member’s guidance. "
                        "Check with your department before acting on it."
                    )
                render_citations(message.get("citations", []))

pending_question = st.session_state.pop("pending_question", None)
typed_question = st.chat_input("Ask about R25, study topics, or general questions")
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
                    {
                        "role": "assistant",
                        "content": small_talk_response,
                        "status": "answered",
                        "answer_type": "small_talk",
                    }
                )
            elif not is_regulation_question(cleaned_question):
                with st.spinner("Putting together a general answer…"):
                    try:
                        answer = generate_general_answer(cleaned_question)
                        st.markdown(answer)
                        st.caption(
                            "General knowledge, not verified against the R25 regulations."
                        )
                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": answer,
                                "answer_type": "general",
                            }
                        )
                    except Exception as error:
                        if isinstance(error, AIServiceError):
                            error_message = str(error)
                        else:
                            logger.exception("Unexpected general-answer failure")
                            error_message = (
                                "I couldn't complete that response. Your question is saved; "
                                "please try again."
                            )
                        st.error(error_message)
                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": error_message,
                                "is_error": True,
                            }
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
                    passages = []
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
                    except Exception as error:
                        if not isinstance(error, AIServiceError):
                            logger.exception("Unexpected regulation-answer failure")
                        citations = [
                            {
                                "pdf_page": passage["pdf_page"],
                                "regulation_page": passage["regulation_page"],
                                "section": passage["section"],
                                "excerpt": passage["excerpt"],
                            }
                            for passage in passages[:3]
                        ]
                        error_message = (
                            "I couldn't generate an AI summary just now, but I found "
                            "these relevant passages in the R25 regulations."
                            if citations
                            else "I couldn't complete that response. Your question is saved; "
                            "please try again."
                        )
                        st.markdown(error_message)
                        if citations:
                            st.caption("AI summary unavailable. Showing matching R25 source text.")
                        render_citations(citations)
                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": error_message,
                                "status": "answered" if citations else "not_found",
                                "answer_type": "regulation_fallback",
                                "citations": citations,
                            }
                        )
