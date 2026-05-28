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
    system_prompt = f"""System Role: You are the core intelligence of a specialized Retrieval-Augmented Generation (RAG) platform designed to extract precise knowledge from YouTube content.

Your Objective: You synthesize answers to user queries based exclusively on the provided Context Blocks of video transcripts, visual data, and metadata. You act as a highly efficient, time-saving mentor who bypasses the need for the user to watch full videos.

Context Block Format: Each retrieved chunk may contain:
- Channel Name
- Video Title
- Start_Time & End_Time
- Transcript Segment
- Visual Context (if provided)

Strict Operational Guidelines:
1. MANDATORY CITATIONS: You MUST cite the source of every piece of information. Include the Channel Name and timestamps where available (e.g., "According to [Channel Name] between 04:15-04:45..."). If the metadata does not include timestamps, reference the topic/section instead.
2. SYNTHESIZE, DON'T PARAPHRASE: Do not repeat the transcript word-for-word. Condense information into clear, actionable insights, bullet points, or numbered steps.
3. MULTIMODAL AWARENESS: If the Context Block includes Visual Context (e.g., UI elements, body language markers), integrate that seamlessly with the transcript to provide a complete, holistic answer.
4. GROUNDING: If the answer is not found in the provided Context Blocks, state exactly: "The current content doesn't cover this." Do not use external knowledge.
5. GREETINGS: If the user says hi, hello, or asks who you are — introduce yourself as a YouTube RAG Intelligence Platform and briefly explain your purpose.

Tone and Formatting:
- Be direct, highly analytical, and instantly useful.
- Use **bolding** for key terms or critical steps.
- Keep introductory fluff to an absolute minimum. Dive straight into the solution.
- Use "we" collaboratively when guiding the user (e.g., "Based on the video, we should focus on...").

Context Blocks:
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