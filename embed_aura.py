"""
Phase 2 — Chunk & Embed: AURA (Charisma on Command)

Run: python embed_aura.py
"""

import json
import hashlib
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
import ollama

TRANSCRIPT_FILE = "charisma_transcripts.json"
COLLECTION_NAME = "aura"
CHUNK_SIZE      = 500
CHUNK_OVERLAP   = 50
BATCH_SIZE      = 100

print("=" * 55)
print("  AURA — Re-embedding Charisma on Command Transcripts")
print("=" * 55)

class NomicEmbeddingFunction:
    def __call__(self, input: list[str]) -> list[list[float]]:
        embeddings = []
        for text in input:
            response = ollama.embeddings(model="nomic-embed-text", prompt=text)
            embeddings.append(response["embedding"])
        return embeddings
        
    def name(self) -> str:
        return "nomic-embed-text"

embed_fn = NomicEmbeddingFunction()

# Load transcripts
with open(TRANSCRIPT_FILE, "r", encoding="utf-8") as f:
    videos = json.load(f)
print(f"✅ Loaded {len(videos)} videos from {TRANSCRIPT_FILE}")

# Set up ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")

# Delete old collection to avoid dimension mismatch
try:
    client.delete_collection(COLLECTION_NAME)
    print(f"✅ Deleted old collection '{COLLECTION_NAME}'")
except Exception:
    pass

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=embed_fn,
    metadata={"hnsw:space": "cosine"}
)
print(f"✅ ChromaDB collection '{COLLECTION_NAME}' ready (using nomic-embed-text)")

# Chunker
splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " "],
)

# Process
ids_batch, docs_batch, metas_batch = [], [], []
total_added = 0

for video in videos:
    if not video.get("transcript"):
        continue

    chunks = splitter.split_text(video["transcript"])
    for i, chunk in enumerate(chunks):
        # Deterministic ID: hash of video_id + chunk_index
        chunk_id = hashlib.md5(f"{video['video_id']}_chunk_{i}".encode()).hexdigest()

        ids_batch.append(chunk_id)
        docs_batch.append(chunk)
        metas_batch.append({
            "video_id":     video["video_id"],
            "title":        video["title"],
            "url":          video["url"],
            "channel_name": video.get("channel_name", "Charisma on Command"),
            "model":        "aura",
        })

        # Batch insert
        if len(ids_batch) >= BATCH_SIZE:
            collection.add(ids=ids_batch, documents=docs_batch, metadatas=metas_batch)
            total_added += len(ids_batch)
            print(f"   📦 Embedded {total_added} chunks so far…")
            ids_batch, docs_batch, metas_batch = [], [], []

# Final batch
if ids_batch:
    collection.add(ids=ids_batch, documents=docs_batch, metadatas=metas_batch)
    total_added += len(ids_batch)

print()
print("=" * 55)
print(f"✅ Done!")
print(f"   Added   : {total_added} new chunks")
print(f"   Total   : {collection.count()} chunks in '{COLLECTION_NAME}'")
print()
print("▶  Next: python api_server.py")
