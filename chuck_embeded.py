import json
import chromadb
from chromadb.utils import embedding_functions
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Load transcripts
with open("charisma_transcripts.json") as f:
    videos = json.load(f)

# Chunker: 500 tokens, 50 overlap
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", ". ", " "]
)

# ChromaDB setup
client = chromadb.PersistentClient(path="./chroma_db")
embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"  # fast, good for RAG
)
collection = client.get_or_create_collection(
    name="charisma_on_command",
    embedding_function=embed_fn
)

# Chunk and store
chunk_id = 0
for video in videos:
    chunks = splitter.split_text(video["transcript"])
    for chunk in chunks:
        collection.add(
            ids=[f"chunk_{chunk_id}"],
            documents=[chunk],
            metadatas=[{
                "video_id": video["video_id"],
                "title": video["title"],    # IMPORTANT: keep this!
                "url": video["url"]
            }]
        )
        chunk_id += 1

print(f"Stored {chunk_id} chunks from {len(videos)} videos")