from pathlib import Path
import os

import streamlit as st
from dotenv import load_dotenv

try:
    from backend.config import PROJECT_DIR, REGULATION_PDF_PATH
    from backend.ingest import extract_pages
    from backend.llm import AIServiceError, generate_answer
    from backend.rag import retrieve_passages
except ModuleNotFoundError:
    from config import PROJECT_DIR, REGULATION_PDF_PATH
    from ingest import extract_pages
    from llm import AIServiceError, generate_answer
    from rag import retrieve_passages

load_dotenv(PROJECT_DIR / ".env")

st.set_page_config(page_title="sahAI — R25 Assistant", layout="wide")

SUGGESTED_QUESTIONS = [
    "What are the attendance requirements to take semester-end exams?",
    "How are internal assessment and semester-end exam marks divided?",
    "How many credits do I need to complete the B.Tech program?",
    "How are SGPA and CGPA calculated?",
]


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
            page_label += f" · Regulation p. {regulation_page}"
        with st.expander(f"{citation['section']} — {page_label}"):
            st.write(citation["excerpt"])


if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("sahAI")
st.caption("MLRITM · MLRS-BT25 academic regulation assistant")

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
    st.subheader("Source document")
    if pages:
        st.success("R25 source ready")
        st.write(f"**MLRS-BT25 Regulations** · {len(pages)} PDF pages")
        st.caption(REGULATION_PDF_PATH.name)
    elif source_error:
        st.error(source_error)
    else:
        st.warning("R25 source PDF not found.")
        st.caption(
            "Place the authorized PDF at "
            "`data/regulations/MLRS-BT25-Regulations.pdf` or set "
            "`SAHAI_REGULATION_PDF`."
        )

    st.divider()
    st.caption(
        "Questions and relevant regulation passages are sent to OpenAI to "
        "generate answers. Avoid entering personal details."
    )
    st.caption(
        "AI-generated guidance can be incomplete. Check important details "
        "against the cited regulation."
    )

if source_error:
    st.error(source_error)
elif not pages:
    st.info(
        "Add the private R25 regulation PDF locally to enable answers. "
        "The source PDF is intentionally excluded from GitHub."
    )

if not st.session_state.messages:
    st.subheader("Questions students often ask")
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
typed_question = st.chat_input("Ask about attendance, marks, credits, or grades…")
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
            if not pages:
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
