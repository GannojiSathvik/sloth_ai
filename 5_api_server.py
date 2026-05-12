import os
import json
import chromadb
from chromadb.utils import embedding_functions
import ollama
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# 1. Initialize Vector Database (Retrieval Engine)
# ---------------------------------------------------------
print("Loading Vector Database (ChromaDB)...")
db_path = "./chroma_db"
client = chromadb.PersistentClient(path=db_path)
embedding_func = embedding_functions.DefaultEmbeddingFunction()

collection_name = "dating_psychology_knowledge"
collection = client.get_collection(
    name=collection_name, 
    embedding_function=embedding_func
)

MODEL_NAME = "gemma4:latest"

# ---------------------------------------------------------
# 2. Data Models
# ---------------------------------------------------------
class ChatRequest(BaseModel):
    message: str

# ---------------------------------------------------------
# 3. API Endpoints
# ---------------------------------------------------------

@app.get("/")
async def get_frontend():
    # Serves the beautiful HTML UI
    return FileResponse("index.html")

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    user_question = request.message
    
    # --- Retrieving Context from ChromaDB ---
    results = collection.query(
        query_texts=[user_question],
        n_results=3  # Get top 3 most relevant paragraphs
    )
    
    retrieved_chunks = results["documents"][0]
    sources = [meta["source"] for meta in results["metadatas"][0]]
    context_text = "\n\n--- NEXT CHUNK ---\n\n".join(retrieved_chunks)
    
    # --- Building the RAG Prompt ---
    system_prompt = f"""You are a domain-specific assistant trained on a curated dataset of communication and social interaction advice.

STRICT RULES:
1. You MUST answer ONLY using the provided context.
2. Do NOT use general knowledge or outside information.
3. If the answer is not clearly found in the context, respond with:
   "Not found in dataset."
4. Use the SAME tone, style, and ideas from the context.
5. Avoid generic advice — be specific to the concepts in the context.
6. If possible, reference techniques, patterns, or ideas mentioned in the context.
7. Keep answers clear, structured, and practical.

RESPONSE STYLE:
- Break into sections if needed
- Use examples if present in context
- Be concise but meaningful

Provided Context:
{context_text}"""

    # --- Streaming Generator for Server-Sent Events (SSE) ---
    def generate_stream():
        try:
            stream = ollama.chat(
                model=MODEL_NAME,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_question}
                ],
                stream=True
            )
            
            # Send the sources first so the UI can display them
            sources_payload = json.dumps({"type": "sources", "sources": list(set(sources))})
            yield f"data: {sources_payload}\n\n"
            
            for chunk in stream:
                content = chunk['message']['content']
                # Stream content
                content_payload = json.dumps({"type": "token", "content": content})
                yield f"data: {content_payload}\n\n"
                
        except Exception as e:
            error_payload = json.dumps({"type": "error", "content": str(e)})
            yield f"data: {error_payload}\n\n"
            
    return StreamingResponse(generate_stream(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*50)
    print("🚀 API Server is starting!")
    print("Open your browser to: http://localhost:8000")
    print("="*50 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)


# python3 5_api_server.py