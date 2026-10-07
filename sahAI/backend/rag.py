import math
import re
from collections import Counter
from typing import Any

STOP_WORDS = {
    "about", "after", "also", "and", "are", "can", "could", "does", "for",
    "from", "have", "how", "into", "is", "its", "may", "more", "what",
    "when", "where", "which", "who", "will", "with", "would", "you", "your",
}


def _tokens(value: str) -> list[str]:
    terms = re.findall(r"[a-z]+|[0-9]+%?", value.lower())
    return [
        term
        for term in terms
        if (len(term) > 2 or term[0].isdigit()) and term not in STOP_WORDS
    ]


def _make_excerpt(text: str, query_terms: list[str], limit: int = 680) -> str:
    content = " ".join(text.split())
    if len(content) <= limit:
        return content

    starts = [0]
    lowered = content.lower()
    for term in query_terms:
        index = lowered.find(term)
        if index >= 0:
            starts.append(max(0, index - 180))

    best_start = 0
    best_score = -1
    for start in starts:
        window = content[start : start + limit].lower()
        score = sum(term in window for term in query_terms)
        if score > best_score:
            best_score = score
            best_start = start

    excerpt = content[best_start : best_start + limit].strip()
    return f"{'…' if best_start else ''}{excerpt}{'…' if best_start + limit < len(content) else ''}"


def retrieve_passages(
    question: str, pages: list[dict[str, Any]], top_k: int = 5
) -> list[dict[str, Any]]:
    """Rank regulation pages with BM25; no external service is used for retrieval."""
    query_terms = list(dict.fromkeys(_tokens(question)))
    if not query_terms or not pages:
        return []

    tokenized_pages = [_tokens(page["text"]) for page in pages]
    document_frequency: Counter[str] = Counter()
    for terms in tokenized_pages:
        document_frequency.update(set(terms))

    average_length = sum(map(len, tokenized_pages)) / max(len(tokenized_pages), 1)
    page_count = len(tokenized_pages)
    k1 = 1.5
    b = 0.75
    ranked: list[tuple[float, dict[str, Any]]] = []

    for page, terms in zip(pages, tokenized_pages):
        frequencies = Counter(terms)
        score = 0.0
        for term in query_terms:
            frequency = frequencies[term]
            if not frequency:
                continue
            doc_frequency = document_frequency[term]
            inverse_document_frequency = math.log(
                1 + (page_count - doc_frequency + 0.5) / (doc_frequency + 0.5)
            )
            length_norm = 1 - b + b * len(terms) / max(average_length, 1)
            score += inverse_document_frequency * (
                frequency * (k1 + 1) / (frequency + k1 * length_norm)
            )
        if score > 0:
            ranked.append((score, page))

    ranked.sort(key=lambda item: item[0], reverse=True)
    return [
        {
            "pdf_page": page["pdf_page"],
            "regulation_page": page["regulation_page"],
            "section": page["section"],
            "text": page["text"][:3600],
            "excerpt": _make_excerpt(page["text"], query_terms),
            "score": round(score, 4),
        }
        for score, page in ranked[:top_k]
    ]
