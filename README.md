[![Live Demo](https://img.shields.io/badge/🚀%20Live%20Demo-chamberlain--secure--view.streamlit.app-6366f1?style=for-the-badge)](https://chamberlain-secure-view.streamlit.app)

# myQ Secure View Assistant

A Retrieval-Augmented Generation (RAG) chatbot that answers questions about Chamberlain Group's myQ Secure View 3-in-1 Smart Lock, launched January 2026.

## What it does

Ask the chatbot any question about the myQ Secure View Smart Lock. The system retrieves the most relevant chunks from Chamberlain's official press release content using semantic search, then Claude generates a grounded answer that cites which source documents it used.

## Architecture

User question -> ChromaDB retrieves top 3 relevant chunks -> Claude (Anthropic) generates a grounded answer using only those chunks -> answer + sources displayed in Streamlit UI.

## Tech Stack

- Python
- Anthropic Claude (Sonnet 4.6)
- ChromaDB (vector database)
- Streamlit (web UI)
- python-dotenv

## Data Source

Documentation in docs/ was sourced from Chamberlain Group's official press release announcing the myQ Secure View 3-in-1 Smart Lock (January 6, 2026):

https://chamberlaingroup.com/press/chamberlain-group-redefines-smart-home-security-with-launch-of-myq-secure-view-3-in-1-smart-lock

## Local Setup

git clone https://github.com/BQ77/chamberlain-rag.git
cd chamberlain-rag
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=your_key_here" > .env
python3 ingest.py
streamlit run app.py
