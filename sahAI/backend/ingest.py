import re
from pathlib import Path
from typing import Any

import pymupdf


def _find_section(lines: list[str], previous: str) -> str:
    for index, line in enumerate(lines[:18]):
        candidate = line.strip()
        if not candidate or "|Page" in candidate:
            continue

        number_only = re.fullmatch(r"(\d{1,2}(?:\.\d{1,2}){0,2})\.?", candidate)
        if number_only and index + 1 < len(lines):
            title = lines[index + 1].strip()
            if title and "|Page" not in title and len(title) <= 110:
                return f"{number_only.group(1)} {title}"[:120]

        numbered_title = re.fullmatch(
            r"(\d{1,2}(?:\.\d{1,2}){0,2})\s+([A-Z][^.!?]{3,105})",
            candidate,
        )
        if numbered_title:
            return f"{numbered_title.group(1)} {numbered_title.group(2)}"[:120]

        if (
            10 <= len(candidate) <= 100
            and re.fullmatch(r"[A-Z][A-Z0-9/&(),: -]+", candidate)
        ):
            return candidate

    return previous


def extract_pages(pdf_path: str | Path) -> list[dict[str, Any]]:
    """Extract text and page references from the private regulation PDF."""
    source = Path(pdf_path).expanduser()
    if not source.is_file():
        raise FileNotFoundError(f"R25 regulation PDF not found: {source}")

    document = pymupdf.open(source)
    pages: list[dict[str, Any]] = []
    current_section = "MLRS-BT25 Academic Regulations"

    try:
        for pdf_page_number, page in enumerate(document, start=1):
            text = page.get_text("text")
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            current_section = _find_section(lines, current_section)
            printed_page = re.search(
                r"^\s*(\d{1,3})\s*\|\s*Page\b", text, re.IGNORECASE | re.MULTILINE
            )

            pages.append(
                {
                    "pdf_page": pdf_page_number,
                    "regulation_page": int(printed_page.group(1))
                    if printed_page
                    else None,
                    "section": current_section,
                    "text": text,
                }
            )
    finally:
        document.close()

    if not pages:
        raise ValueError("The R25 regulation PDF contains no pages.")
    if not any(page["text"].strip() for page in pages):
        raise ValueError("No searchable text was found in the R25 regulation PDF.")

    return pages
