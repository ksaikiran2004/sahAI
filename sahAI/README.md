# sahAI — MLRS-BT25 Assistant

A Streamlit FAQ assistant for MLRITM students. It retrieves passages from the
MLRS-BT25 regulations and asks OpenAI to explain them in plain language, with
citations to both the PDF page and the printed regulation page when available.

## Run locally

1. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Put an authorized copy of the regulation PDF at
   `data/regulations/MLRS-BT25-Regulations.pdf`. This folder is ignored by Git;
   the PDF and its contents are not part of this public repository.

3. Set `OPENAI_API_KEY` in your environment or in a local `.env` file. Never
   commit the key. Optionally set `OPENAI_MODEL` or `SAHAI_REGULATION_PDF`.

4. Start the assistant from this directory:

   ```bash
   streamlit run backend/app.py --server.port 8501
   ```

The app extracts searchable text from the PDF locally. Only the current
question and the most relevant regulation passages are sent to OpenAI to
generate an answer. If the document does not support an answer, sahAI says so
instead of guessing.

Answers are AI-generated guidance, not an official decision. Students should
check the cited regulation and confirm case-specific questions with their
department.
