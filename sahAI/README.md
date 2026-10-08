# sahAI — MLRS-BT25 Assistant

A Streamlit assistant for MLRITM R25 CSM students. It retrieves passages
from the MLRS-BT25 regulations and asks Gemini 3.8 Flash to explain them in
plain language, with citations to both the PDF page and the printed regulation
page when available.

## Run locally

1. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Ensure the regulation PDF is available at
   `data/regulations/MLRS-BT25-Regulations.pdf`.

3. Create a Gemini API key in Google AI Studio and set `GEMINI_API_KEY` in your
   environment or in a local `.env` file. Never commit the key. Optionally set
   `GEMINI_MODEL` (defaults to `gemini-3.8-flash`) or `SAHAI_REGULATION_PDF`.

4. Start the assistant from this directory:

   ```bash
   streamlit run backend/app.py --server.port 8501
   ```

   If you are working from the repository root instead, use:

   ```bash
   streamlit run sahAI/backend/app.py --server.port 8501
   ```

The app extracts searchable text from the PDF locally. Only the current
question and the most relevant regulation passages are sent to Google Gemini to
generate an answer. If the document does not support an answer, sahAI says so
instead of guessing.

Answers are AI-generated guidance, not an official decision. Students should
check the cited regulation and confirm case-specific questions with their
department.

## Streamlit Community Cloud

Create the app from the repository and use `sahAI/backend/app.py` as the main
file. Add `GEMINI_API_KEY = "your-key"` in the app's Secrets settings. Keep the
regulation PDF at `sahAI/data/regulations/MLRS-BT25-Regulations.pdf` in the
deployment repository.
