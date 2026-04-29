"""
app.py — Streamlit web UI for the myQ Secure View RAG assistant.

Run with: streamlit run app.py
"""

import streamlit as st
from anthropic import Anthropic
from dotenv import load_dotenv
import chromadb

# Page config
st.set_page_config(
    page_title="myQ Secure View Assistant",
    page_icon="🔒",
    layout="centered",
)

# Load API key
load_dotenv()


# Initialize clients once (cached across reruns)
@st.cache_resource
def get_clients():
    anthropic_client = Anthropic()
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    collection = chroma_client.get_or_create_collection(name="secure_view_docs")
    return anthropic_client, collection


anthropic_client, collection = get_clients()

# Title and description
st.title("🔒 myQ Secure View Assistant")
st.caption(
    "Ask me anything about Chamberlain Group's myQ Secure View 3-in-1 Smart Lock "
    "(launched January 2026). Powered by RAG over Chamberlain's official press release."
)

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display existing chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and "sources" in msg:
            st.caption(f"Sources: {', '.join(msg['sources'])}")

# Chat input at the bottom
if user_input := st.chat_input("Ask about the Secure View..."):
    # Add user message to history and display it
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # STEP 1: Retrieve top 3 relevant chunks from ChromaDB
    results = collection.query(
        query_texts=[user_input],
        n_results=3,
    )
    relevant_chunks = results["documents"][0]
    sources = list({m["source"] for m in results["metadatas"][0]})

    # STEP 2: Build context from chunks
    context = "\n\n---\n\n".join(relevant_chunks)

    # STEP 3: Build system prompt with retrieved context
    system_prompt = f"""You are a helpful assistant that answers questions about Chamberlain Group's myQ Secure View 3-in-1 Smart Lock.

Use ONLY the following retrieved documentation to answer questions. If the answer is not in the documents, say "I do not have that information in my documentation."

Retrieved documentation:
{context}
"""

    # STEP 4: Build message list for the API
    api_messages = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    ]

    # STEP 5: Call Claude (with a spinner while waiting)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = anthropic_client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=system_prompt,
                messages=api_messages,
            )
            answer = response.content[0].text

        # Display answer and sources
        st.markdown(answer)
        st.caption(f"Sources: {', '.join(sources)}")

    # Save assistant message to history
    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": sources}
    )
