# sahAI

An academic regulation assistant for MLRITM students, focused on the
MLRS-BT25 (R25) B.Tech regulations.

The Streamlit app lives in [`sahAI/backend/app.py`](sahAI/backend/app.py). It
retrieves relevant passages from the R25 PDF in `sahAI/data/regulations/` and
uses Gemini 3.8 Flash by default to produce cited answers.

Never commit `.env` or API keys. The repository-root `.gitignore` excludes
local secrets. See [`sahAI/README.md`](sahAI/README.md) for setup and cloud
deployment instructions.

## Run from the repo root

```bash
cd /workspaces/sahAI
streamlit run sahAI/backend/app.py --server.headless true --server.port 8501
```

## Deploy to Streamlit Community Cloud

Create an app from this GitHub repository and set the main file to
` sahAI/backend/app.py`. Add the key under the app's Secrets settings:

```toml
GEMINI_API_KEY = "your-key"
```

The app reads the key from Streamlit Secrets in the cloud and from `.env` or
the process environment locally. Keep the regulation PDF in the repository at
`sahAI/data/regulations/MLRS-BT25-Regulations.pdf` for deployment.

You can also run it from inside the project folder:

```bash
cd /workspaces/sahAI/sahAI
streamlit run backend/app.py --server.port 8501
```
