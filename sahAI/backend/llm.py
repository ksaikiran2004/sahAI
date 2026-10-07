import json
import os
from typing import Any

from openai import APIConnectionError, APIStatusError, OpenAI

try:
    from .config import OPENAI_MODEL
except ImportError:
    from config import OPENAI_MODEL


class AIServiceError(RuntimeError):
    """A safe, user-facing error from the answer service."""


def generate_answer(
    question: str, passages: list[dict[str, Any]]
) -> dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise AIServiceError(
            "The answer service is not configured. Add OPENAI_API_KEY to your "
            "environment or platform secrets."
        )

    client = OpenAI(api_key=api_key)
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
        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            response_format={"type": "json_object"},
            max_completion_tokens=1400,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are sahAI, an assistant for students asking about "
                        "MLRITM's MLRS-BT25 B.Tech regulations. Answer only from "
                        "the supplied passages. Do not use outside knowledge or "
                        "guess. Explain the rule clearly and preserve important "
                        "conditions, thresholds, dates, and exceptions. If the "
                        "passages do not directly support an answer, set status "
                        "to not_found and say you could not verify it from this "
                        "document. Return JSON only with fields: answer (string), "
                        "status (answered or not_found), citedPdfPages (array of "
                        "supplied PDF page numbers), and needsHumanReview (boolean). "
                        "Cite only supplied pages and do not put citations inside "
                        "the answer text. Set needsHumanReview true for unanswered, "
                        "ambiguous, or case-specific policy questions."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {"question": question, "regulationPassages": evidence},
                        ensure_ascii=False,
                    ),
                },
            ],
        )
    except APIStatusError as error:
        code = getattr(error, "code", None)
        status = getattr(error, "status_code", None)
        if status == 429 and code in {
            "credit_balance_exhausted",
            "insufficient_quota",
        }:
            raise AIServiceError(
                "The OpenAI account connected to sahAI has run out of API credits. "
                "Add billing or credits to that account, then try again."
            ) from None
        if status == 429:
            raise AIServiceError(
                "OpenAI is rate-limiting requests. Wait a moment, then try again."
            ) from None
        if status in {401, 403}:
            raise AIServiceError(
                "The OpenAI key configured for sahAI is not authorized. Update "
                "OPENAI_API_KEY in your platform secrets."
            ) from None
        raise AIServiceError(
            "OpenAI could not answer right now. Please try again shortly."
        ) from None
    except APIConnectionError:
        raise AIServiceError(
            "sahAI could not connect to OpenAI. Check your connection and try again."
        ) from None

    content = completion.choices[0].message.content
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
