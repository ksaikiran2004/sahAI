import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_PDF_PATH = PROJECT_DIR / "data" / "regulations" / "MLRS-BT25-Regulations.pdf"
LEGACY_PDF_PATHS = [
    PROJECT_DIR / "MLRS-BT25-Regulations.pdf",
    PROJECT_DIR / "MLRS_B.Tech_BT25_Regulations.pdf",
    PROJECT_DIR / "MLRS_B.Tech_BT25_Regulations (2).pdf",
]


def resolve_regulation_pdf_path() -> Path:
    configured = os.getenv("SAHAI_REGULATION_PDF")
    if configured:
        candidate = Path(configured).expanduser()
        if candidate.is_absolute():
            return candidate
        return PROJECT_DIR / candidate

    for candidate in [DEFAULT_PDF_PATH, *LEGACY_PDF_PATHS]:
        if candidate.is_file():
            return candidate

    return DEFAULT_PDF_PATH


REGULATION_PDF_PATH = resolve_regulation_pdf_path()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
