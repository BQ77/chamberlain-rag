"""
app.py — Streamlit web UI for the myQ Secure View RAG assistant.

Run with: streamlit run app.py
"""

import streamlit as st
from anthropic import Anthropic
from dotenv import load_dotenv
import chromadb
from pathlib import Path

# Page config
st.set_page_config(
    page_title="myQ Secure View Assistant",
    page_icon="🔒",
    layout="centered",
)

load_dotenv()

# Absolute path to docs folder (works on any deployment)
SCRIPT_DIR = Path(__file__).parent
DOCS_DIR = SCRIPT_DIR / "docs"


def auto_ingest(collection):
    """Build the vector DB from docs/ if it's empty."""
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


@st.cache_resource
def get_clients():
    anthropic_client = Anthropic()
    chroma_client = chromadb.Client()
    collection = chroma_client.get_or_create_collection(name="secure_view_docs")
    auto_ingest(collection)
    return anthropic_client, collection


anthropic_client, collection = get_clients()

# Debug sidebar
st.sidebar.write(f"📊 Database: {collection.count()} chunks")

st.title("🔒 myQ Secure View Assistant")
st.caption(
    "Ask me anything about Chamberlain Group's myQ Secure View 3-in-1 Smart Lock "
    "(launched January 2026). Powered by RAG over Chamberlain's official press release."
)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and "sources" in msg:
            st.caption(f"Sources: {', '.join(msg['sources'])}")

if user_input := st.chat_input("Ask about the Secure View..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    results = collection.query(query_texts=[user_input], n_results=5)
    relevant_chunks = results["documents"][0]
    sources = list({m["source"] for m in results["metadatas"][0]})

    context = "\n\n---\n\n".join(relevant_chunks)

    system_prompt = f"""You are a helpful assistant that answers questions about Chamberlain Group and their myQ Secure View 3-in-1 Smart Lock.

Use the following retrieved documentation as your primary source. Answer questions naturally using this context. If the specific answer truly is not in the documentation, say "I do not have that information in my documentation."

Retrieved documentation:
{context}
"""

    api_messages = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    ]

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = anthropic_client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=system_prompt,
                messages=api_messages,
            )
            answer = response.content[0].text

        st.markdown(answer)
        st.caption(f"Sources: {', '.join(sources)}")

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": sources}
    )