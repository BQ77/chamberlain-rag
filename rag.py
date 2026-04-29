"""
rag.py — Chat with the Secure View RAG assistant.

Combines ChromaDB semantic retrieval with Claude for grounded answers.
Each user question retrieves the top 3 most relevant chunks from the docs,
then Claude answers using ONLY those chunks (no hallucinations).
"""

import os
from anthropic import Anthropic
from dotenv import load_dotenv
import chromadb

# Load ANTHROPIC_API_KEY from .env
load_dotenv()
client = Anthropic()

# Connect to ChromaDB and load our Secure View collection
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="secure_view_docs")

print("Hi! I'm the myQ Secure View assistant.")
print("Ask me anything about Chamberlain's new 3-in-1 Smart Lock.")
print("Type 'quit' to exit.\n")

# Conversation history (so Claude remembers context across turns)
conversation_history = []

while True:
    user_input = input("You: ")

    # Exit on 'quit'
    if user_input.lower() == "quit":
        print("Bye!")
        break

    # Skip empty input
    if user_input.strip() == "":
        print("(Please type something.)\n")
        continue

    # STEP 1: Retrieve top 3 most relevant chunks from ChromaDB
    results = collection.query(
        query_texts=[user_input],
        n_results=3,
    )
    relevant_chunks = results["documents"][0]
    sources = results["metadatas"][0]

    # STEP 2: Build a context string from the retrieved chunks
    context = "\n\n---\n\n".join(relevant_chunks)

    # STEP 3: Build the system prompt with the retrieved context
    system_prompt = f"""You are a helpful assistant that answers questions about Chamberlain Group's myQ Secure View 3-in-1 Smart Lock.

Use ONLY the following retrieved documentation to answer questions. If the answer is not in the documents, say "I do not have that information in my documentation."

Retrieved documentation:
{context}
"""

    # STEP 4: Add the user message to conversation history
    conversation_history.append({"role": "user", "content": user_input})

    # STEP 5: Call Claude with the system prompt + history
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system_prompt,
        messages=conversation_history,
    )

    # STEP 6: Extract Claude's answer and save it to history
    assistant_message = response.content[0].text
    conversation_history.append({"role": "assistant", "content": assistant_message})

    # STEP 7: Print the answer + show which docs it came from
    print(f"\nClaude: {assistant_message}")
    print(f"\n(Sources: {[s['source'] for s in sources]})\n")
