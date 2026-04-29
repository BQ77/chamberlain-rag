"""
app.py — Streamlit web UI for the myQ Secure View RAG assistant.
Run with: streamlit run app.py
"""

import streamlit as st
from anthropic import Anthropic
from dotenv import load_dotenv
import chromadb
from pathlib import Path

st.set_page_config(
    page_title="myQ Secure View Assistant",
    page_icon="🔒",
    layout="centered",
)

load_dotenv()

SCRIPT_DIR = Path(__file__).parent
DOCS_DIR = SCRIPT_DIR / "docs"


def auto_ingest(collection):
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

# ===== SIDEBAR =====
with st.sidebar:
    st.markdown("## 🔒 About this assistant")
    st.markdown(
        "Ask questions about Chamberlain Group's **myQ Secure View 3-in-1 Smart Lock** "
        "(launched January 2026)."
    )
    st.markdown("---")
    st.markdown("### 💡 Try asking")
    example_questions = [
        "What is the myQ Secure View?",
        "How does AI detection work?",
        "What entry methods does it support?",
        "When was it launched?",
        "How fast does it unlock?",
        "What myQ accessories does it work with?",
    ]
    for q in example_questions:
        if st.button(q, use_container_width=True, key=f"ex_{q}"):
            st.session_state.example_clicked = q

    st.markdown("---")
    st.markdown(
        "### 🛠️ Built with\n"
        "- Anthropic Claude\n"
        "- ChromaDB (vector DB)\n"
        "- Streamlit\n"
        "- Python"
    )
    st.markdown("---")
    st.caption(
        "Source: Chamberlain Group official press release. "
        "[Read it](https://chamberlaingroup.com/press/chamberlain-group-redefines-smart-home-security-with-launch-of-myq-secure-view-3-in-1-smart-lock)"
    )

# ===== MAIN UI =====
st.title("🔒 myQ Secure View Assistant")
st.caption(
    "RAG chatbot grounded in Chamberlain's official press release. "
    "Ask anything about the new 3-in-1 Smart Lock."
)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and "sources" in msg:
            st.caption(f"📚 Sources: {', '.join(msg['sources'])}")

# Handle example button click OR user typing
user_input = st.chat_input("Ask about the Secure View...")
if "example_clicked" in st.session_state:
    user_input = st.session_state.pop("example_clicked")

if user_input:
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
        st.caption(f"📚 Sources: {', '.join(sources)}")

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": sources}
    )