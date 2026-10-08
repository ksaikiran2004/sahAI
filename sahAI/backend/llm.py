import json
import os
from typing import Any

from google import genai
from google.genai import errors, types

try:
    from .config import GEMINI_MODEL
except ImportError:
    from config import GEMINI_MODEL


class AIServiceError(RuntimeError):
    """A safe, user-facing error from the answer service."""


def _get_api_key() -> str | None:
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        return api_key

    try:
        import streamlit as st

        return st.secrets.get("GEMINI_API_KEY")
    except Exception:
        return None


def _api_error_message(status: int | None) -> str:
    if status == 429:
        return (
            "The Gemini API quota or rate limit has been reached. Check your "
            "Google AI Studio project, then try again."
        )
    if status in {401, 403}:
        return (
            "The Gemini API key configured for sahAI is not authorized. Update "
            "GEMINI_API_KEY in your environment or platform secrets."
        )
    if status == 503:
        return "Gemini is temporarily experiencing high demand. Please try again shortly."
    return "Gemini could not answer right now. Please try again shortly."


def generate_general_answer(question: str) -> str:
    api_key = _get_api_key()
    if not api_key:
        raise AIServiceError(
            "The answer service is not configured. Add GEMINI_API_KEY to your "
            "environment or platform secrets."
        )

    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=question,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are sahAI, a helpful assistant for students. Answer basic "
                    "general-knowledge and educational questions clearly and "
                    "concisely. Do not invent current facts. Do not provide "
                    "institution-specific rules or R25 policy; those require "
                    "the supplied regulation document. For uncertain or high-stakes "
                    "questions, state the limitation and recommend an appropriate "
                    "authoritative source."
                ),
                max_output_tokens=700,
            ),
        )
    except errors.APIError as error:
        raise AIServiceError(_api_error_message(getattr(error, "code", None))) from None

    answer = (response.text or "").strip()
    if not answer:
        raise AIServiceError(
            "The answer service returned an empty response. Please try again."
        )
    return answer


def generate_answer(
    question: str, passages: list[dict[str, Any]]
) -> dict[str, Any]:
    api_key = _get_api_key()
    if not api_key:
        raise AIServiceError(
            "The answer service is not configured. Add GEMINI_API_KEY to your "
            "environment or platform secrets."
        )

    client = genai.Client(api_key=api_key)
    evidence = [
        {
            "pdfPage": passage["pdf_page"],
            "regulationPage": passage["regulation_page"],
            "section": passage["section"],
            "text": passage["text"],
        }
        for passage in passages
    ]

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=json.dumps(
                {"question": question, "regulationPassages": evidence},
                ensure_ascii=False,
            ),
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are sahAI, an assistant for MLRITM R25 CSM students "
                    "asking about the MLRS-BT25 B.Tech regulations. Answer only "
                    "from the supplied passages. Do not use outside knowledge "
                    "or guess. Explain the rule clearly and preserve important "
                    "conditions, thresholds, dates, and exceptions. If the "
                    "passages do not directly support an answer, set status to "
                    "not_found and say you could not verify it from this document. "
                    "Cite only supplied PDF pages. Set needsHumanReview true for "
                    "unanswered, ambiguous, or case-specific policy questions."
                ),
                response_mime_type="application/json",
                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "answer": {"type": "STRING"},
                        "status": {
                            "type": "STRING",
                            "enum": ["answered", "not_found"],
                        },
                        "citedPdfPages": {
                            "type": "ARRAY",
                            "items": {"type": "INTEGER"},
                        },
                        "needsHumanReview": {"type": "BOOLEAN"},
                    },
                    "required": [
                        "answer",
                        "status",
                        "citedPdfPages",
                        "needsHumanReview",
                    ],
                },
                max_output_tokens=1400,
            ),
        )
    except errors.APIError as error:
        status = getattr(error, "code", None)
        raise AIServiceError(_api_error_message(status)) from None

    content = response.text
    try:
        parsed = json.loads(content or "")
    except json.JSONDecodeError:
        raise AIServiceError(
            "The answer service returned an unreadable response. Please try again."
        ) from None

    if not isinstance(parsed, dict) or not isinstance(parsed.get("answer"), str):
        raise AIServiceError(
            "The answer service returned an incomplete response. Please try again."
        )

    status = parsed.get("status")
    needs_review = parsed.get("needsHumanReview")
    cited_pages = parsed.get("citedPdfPages")
    if (
        status not in {"answered", "not_found"}
        or not isinstance(needs_review, bool)
        or not isinstance(cited_pages, list)
        or not all(isinstance(page, int) for page in cited_pages)
    ):
        raise AIServiceError(
            "The answer service returned an invalid response. Please try again."
        )

    passage_by_page = {passage["pdf_page"]: passage for passage in passages}
    citations = [
        {
            "pdf_page": page,
            "regulation_page": passage_by_page[page]["regulation_page"],
            "section": passage_by_page[page]["section"],
            "excerpt": passage_by_page[page]["excerpt"],
        }
        for page in cited_pages
        if page in passage_by_page
    ][:3]

    has_grounded_answer = status == "answered" and bool(citations)
    if status == "answered" and not citations:
        answer = (
            "I found related passages, but couldn’t verify an answer with a "
            "reliable citation. Please check with your department."
        )
    else:
        answer = parsed["answer"].strip()

    return {
        "answer": answer,
        "status": "answered" if has_grounded_answer else "not_found",
        "citations": citations,
        "needs_human_review": needs_review or not has_grounded_answer,
    }
