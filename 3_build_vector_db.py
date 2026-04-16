import json
import os
import chromadb
from chromadb.utils import embedding_functions

# 1. Initialize ChromaDB Client
# This will create a persistent folder named "chroma_db" in the current directory
db_path = "./chroma_db"
print(f"Initializing ChromaDB at {db_path}...")
client = chromadb.PersistentClient(path=db_path)

# 2. Choose the Embedding Model
# We're using the default efficient local model: all-MiniLM-L6-v2
# It downloads automatically the first time and runs locally!
print("Setting up embedding function...")
embedding_func = embedding_functions.DefaultEmbeddingFunction()

# 3. Create or Get the Collection
collection_name = "dating_psychology_knowledge"
collection = client.get_or_create_collection(
    name=collection_name,
    embedding_function=embedding_func
)

# 4. Load the Data
data_path = "training_data.json"
print(f"Loading data from {data_path}...")
with open(data_path, "r") as f:
    data = json.load(f)

# 5. Insert Data into ChromaDB
print("Ingesting chunks into the vector database (this might take a few seconds on the first run)...")
# We'll batch them to make insertion organized
documents = []
metadatas = []
ids = []

for idx, item in enumerate(data):
    # The 'input' field has the actual chunk text
    text_chunk = item.get("input", "")
    source_file = item.get("source", "unknown")
    
    if text_chunk:
        documents.append(text_chunk)
        # We save metadata so the AI knows WHICH video the chunk came from
        metadatas.append({"source": source_file, "chunk_id": str(idx)})
        # Chroma requires a unique string ID for every document
        ids.append(f"chunk_{idx}")

# Perform the insertion
if documents:
    collection.upsert(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    print(f"✅ Successfully ingested {len(documents)} chunks into ChromaDB!")

# 6. Verify with a Test Query
print("\n" + "="*60)
print("TESTING THE VECTOR DATABASE")
print("="*60)
# We test what the database retrieves when asked a human question
query = "How do you avoid running out of things to say?"
print(f'Query -> "{query}"\n')

results = collection.query(
    query_texts=[query],
    n_results=1  # Get the single most relevant chunk
)

if results["documents"] and len(results["documents"][0]) > 0:
    retrieved_chunk = results["documents"][0][0]
    retrieved_source = results["metadatas"][0][0]["source"]
    print(f"🎯 MATCH FOUND from {retrieved_source}:")
    print("-" * 40)
    print(retrieved_chunk[:300] + "... [truncated]")
else:
    print("No chunks retrieved.")
    
print("="*60)
print("VECTOR DB IS READY FOR THE RAG CHATBOT!")
print("="*60)
