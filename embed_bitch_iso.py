"""
Phase 2 — Chunk & Embed: BITCH ISO (Dark Feminine Channel)

pip install chromadb sentence-transformers langchain-text-splitters

1. Put your bitch_iso transcripts JSON at: bitch_iso_transcripts.json
   Format: same as charisma_transcripts.json — list of:
   { "video_id", "title", "url", "channel_name", "transcript" }

2. Run: python embed_bitch_iso.py
"""

import json
import hashlib
import os
import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter

TRANSCRIPT_FILE = "bitch_iso_transcripts.json"
COLLECTION_NAME = "bitch_iso"
MODEL_NAME      = "all-MiniLM-L6-v2"
CHUNK_SIZE      = 500
CHUNK_OVERLAP   = 50
BATCH_SIZE      = 100

print("=" * 55)
print("  BITCH ISO — Embedding Dark Feminine Transcripts")
print("=" * 55)

if not os.path.exists(TRANSCRIPT_FILE):
    print(f"❌ {TRANSCRIPT_FILE} not found.")
    print("   Run your transcript extractor script for the Bitch Iso channel first.")
    print("   The output file must be named: bitch_iso_transcripts.json")
    exit(1)

with open(TRANSCRIPT_FILE, "r", encoding="utf-8") as f:
    videos = json.load(f)
print(f"✅ Loaded {len(videos)} videos from {TRANSCRIPT_FILE}")

client = chromadb.PersistentClient(path="./chroma_db")
embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=MODEL_NAME
)
collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=embed_fn,
    metadata={"hnsw:space": "cosine"}
)
print(f"✅ ChromaDB collection '{COLLECTION_NAME}' ready ({collection.count()} existing chunks)")

existing_ids = set()
existing = collection.get(include=[])
if existing and existing["ids"]:
    existing_ids = set(existing["ids"])
print(f"   Skipping {len(existing_ids)} already-embedded chunks")

splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " "],
)

ids_batch, docs_batch, metas_batch = [], [], []
total_added = skipped = 0

for video in videos:
    if not video.get("transcript"):
        continue

    chunks = splitter.split_text(video["transcript"])
    for i, chunk in enumerate(chunks):
        chunk_id = hashlib.md5(f"{video['video_id']}_chunk_{i}".encode()).hexdigest()

        if chunk_id in existing_ids:
            skipped += 1
            continue

        ids_batch.append(chunk_id)
        docs_batch.append(chunk)
        metas_batch.append({
            "video_id":     video["video_id"],
            "title":        video["title"],
            "url":          video["url"],
            "channel_name": video.get("channel_name", "Bitch Iso Channel"),
            "model":        "bitch_iso",
        })

        if len(ids_batch) >= BATCH_SIZE:
            collection.add(ids=ids_batch, documents=docs_batch, metadatas=metas_batch)
            total_added += len(ids_batch)
            print(f"   📦 Embedded {total_added} chunks so far…")
            ids_batch, docs_batch, metas_batch = [], [], []

if ids_batch:
    collection.add(ids=ids_batch, documents=docs_batch, metadatas=metas_batch)
    total_added += len(ids_batch)

print()
print("=" * 55)
print(f"✅ Done!")
print(f"   Added   : {total_added} new chunks")
print(f"   Skipped : {skipped} (already embedded)")
print(f"   Total   : {collection.count()} chunks in '{COLLECTION_NAME}'")
