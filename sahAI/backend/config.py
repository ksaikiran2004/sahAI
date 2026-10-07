import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_PDF_PATH = PROJECT_DIR / "data" / "regulations" / "MLRS-BT25-Regulations.pdf"

configured_pdf_path = Path(
    os.getenv("SAHAI_REGULATION_PDF", str(DEFAULT_PDF_PATH))
).expanduser()
REGULATION_PDF_PATH = (
    configured_pdf_path
    if configured_pdf_path.is_absolute()
    else PROJECT_DIR / configured_pdf_path
)

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
