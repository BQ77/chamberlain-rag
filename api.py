"""
api.py — FastAPI REST endpoint for the myQ Secure View RAG assistant.

Run locally:  python -m uvicorn api:app --reload --port 8000
Test:         curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"question": "What is the Secure View?"}'
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from anthropic import Anthropic
from dotenv import load_dotenv
import chromadb
from pathlib import Path

load_dotenv()

app = FastAPI(
    title="myQ Secure View RAG API",
    description="REST endpoint for the Chamberlain Secure View RAG assistant.",
    version="1.0.0",
)

# Absolute paths
SCRIPT_DIR = Path(__file__).parent
DOCS_DIR = SCRIPT_DIR / "docs"

# Initialize clients ONCE at startup
anthropic_client = Anthropic()
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(name="secure_view_docs")


def auto_ingest():
    """Build the vector DB from docs/ on first startup."""
    if collection.count() > 0:
        return
    for doc_file in DOCS_DIR.glob("*.txt"):
        with open(doc_file, "r") as f:
            text = f.read()
        chunks = [p.strip() for p in text.split("\n\n") if p.strip()]
        for i, chunk in enumerate(chunks):
            collection.add(
                ids=[f"{doc_file.stem}_chunk_{i}"],
                documents=[chunk],
                metadatas=[{"source": doc_file.name, "chunk_index": i}],
            )


# Run ingestion on startup
auto_ingest()


# Request/response models
class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]


@app.get("/")
def root():
    return {
        "name": "myQ Secure View RAG API",
        "status": "running",
        "chunks_loaded": collection.count(),
        "endpoints": {
            "POST /chat": "Send a question, get a grounded answer with sources",
            "GET /health": "Health check",
        },
    }


@app.get("/health")
def health():
    return {"status": "ok", "chunks": collection.count()}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # Retrieve top 5 chunks
    results = collection.query(query_texts=[request.question], n_results=5)
    relevant_chunks = results["documents"][0]
    sources = list({m["source"] for m in results["metadatas"][0]})

    context = "\n\n---\n\n".join(relevant_chunks)

    system_prompt = f"""You are a helpful assistant that answers questions about Chamberlain Group and their myQ Secure View 3-in-1 Smart Lock.

Use the following retrieved documentation as your primary source. Answer questions naturally using this context. If the specific answer truly is not in the documentation, say "I do not have that information in my documentation."

Retrieved documentation:
{context}
"""

    response = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": request.question}],
    )

    answer = response.content[0].text
    return ChatResponse(answer=answer, sources=sources)
