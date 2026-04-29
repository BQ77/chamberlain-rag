#Importing this lib which we downloaded
import chromadb

#made a client so it can talk to vector database and made it persistent bec we
# wanna save the data and then give it a path to a foldername we want
client = chromadb.PersistentClient(path="./chroma_db")
#collection is a drawer in database we said either create it by the name myq_docs or find existing 
#we need it because dont want things messy make a separate drawer for docs
collection = client.get_or_create_collection(name="myq_docs")

# Stage 3: Read one file and chunk it by paragraph

# Read the entire file as a string
with open("docs/myq_overview.txt", "r") as f:
    text = f.read()

# Split the text into paragraphs by double quotes on each line
paragraphs = text.split("\n\n")

# Filter out any empty paragraphs remove them and just text should stay
chunks = [p.strip() for p in paragraphs if p.strip()]
#after removing the empty lines. cound the number of lines/ chunks
print(f"Split myq_overview.txt into {len(chunks)} chunks")

# Add each chunk to the collection(drawer) with a unique ID , and document
for i, chunk in enumerate(chunks):
    chunk_id = f"myq_overview_chunk_{i}"
    collection.add(
        ids=[chunk_id],
        documents=[chunk],
    )
#number of chunks with unique id stored in collection
print(f"Done! Collection now has {collection.count()} items.")

# Test it with a query we want 2 closes results, it will embed 
results = collection.query(
    query_texts=["What devices does it work with?"],
    n_results=2,
)

print("\nQuery: 'What devices does it work with?'")
# a for loop gave i and doc variables, i means iteration =0 and doc ( we said to print lines/results)
# enumerate bec we want the position along with the chunk and then we did results bec 
# we said the vector u saved find in it documents and gave us the first list in docouments
for i, doc in enumerate(results["documents"][0]):
    # for better readability
    print(f"\nResult {i+1}:")
    print(doc)