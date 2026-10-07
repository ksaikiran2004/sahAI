# sahAI

An academic regulation assistant for MLRITM students, focused on the
MLRS-BT25 (R25) B.Tech regulations.

The Streamlit app lives in [`sahAI/`](sahAI/). It retrieves relevant passages
from a local, private copy of the R25 PDF and uses OpenAI to produce cited
answers.

The PDF, extracted regulation text, and `OPENAI_API_KEY` are intentionally not
stored in this public repository. See [`sahAI/README.md`](sahAI/README.md) for
setup and run instructions.
