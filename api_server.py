"""
Sloth AI — API Server (AURA + BITCH ISO)

pip install fastapi uvicorn chromadb sentence-transformers ollama

Run: python api_server.py
"""

import json
import re
import chromadb
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import ollama

app = FastAPI(title="Sloth AI RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── ChromaDB ───────────────────────────────────────────────────────────────────

print("🔧 Loading ChromaDB…")
db_client = chromadb.PersistentClient(path="./chroma_db")
class NomicEmbeddingFunction:
    def __call__(self, input: list[str]) -> list[list[float]]:
        embeddings = []
        for text in input:
            response = ollama.embeddings(model="nomic-embed-text", prompt=text)
            embeddings.append(response["embedding"])
        return embeddings
        
    def embed_query(self, input: list[str]) -> list[list[float]]:
        return self.__call__(input)
        
    def embed_documents(self, input: list[str]) -> list[list[float]]:
        return self.__call__(input)
        
    def name(self) -> str:
        return "nomic-embed-text"

embed_fn = NomicEmbeddingFunction()

COLLECTIONS = {}
for name in ["aura", "bitch_iso"]:
    try:
        COLLECTIONS[name] = db_client.get_collection(name=name, embedding_function=embed_fn)
        print(f"  ✅ Collection '{name}': {COLLECTIONS[name].count()} chunks loaded")
    except Exception:
        print(f"  ⚠️  Collection '{name}' not found — run embed_{name}.py first")

OLLAMA_MODEL = "mistral-small3.1"

# ── Intent Router ──────────────────────────────────────────────────────────────

GREETINGS = {
    "hello", "hi", "hey", "sup", "yo", "hiya", "howdy",
    "what's up", "whats up", "wassup", "good morning",
    "good evening", "good afternoon", "good night",
    "how are you", "how r u", "how are u", "what's good",
}

QUESTION_SIGNALS = {"how", "what", "why", "when", "who", "where", "tell", "explain",
                    "give", "show", "help", "teach", "tips", "advice", "ways"}

def classify_intent(message: str) -> str:
    """Returns 'small_talk' or 'knowledge_query'."""
    msg = message.lower().strip().rstrip("?!.,")
    words = msg.split()

    if msg in GREETINGS:
        return "small_talk"

    # Short message (≤3 words) with no question words = likely small talk
    if len(words) <= 3 and not any(w in QUESTION_SIGNALS for w in words):
        return "small_talk"

    return "knowledge_query"


# ── Small Talk Responses ───────────────────────────────────────────────────────

SMALL_TALK = {
    "aura": {
        "default": "Hey! I'm AURA — trained on Charisma on Command's content. Ask me about confidence, first impressions, body language, or social skills.",
        "how are you": "I'm good! Ready to help. What social situation do you want to navigate?",
        "what's up": "Not much — just waiting to help you level up your social game. What's on your mind?",
    },
    "bitch_iso": {
        "default": "Hey. I'm Bitch Iso. Ask me about standards, feminine energy, boundaries, or mindset. What do you need?",
        "how are you": "Unbothered, as always. What are we working through?",
        "what's up": "You tell me. What's the situation?",
    },
}

def get_small_talk_response(message: str, model: str) -> str:
    msg = message.lower().strip().rstrip("?!.,")
    responses = SMALL_TALK.get(model, SMALL_TALK["aura"])
    return responses.get(msg, responses["default"])


# ── System Prompts ─────────────────────────────────────────────────────────────

SYSTEM_PROMPTS = {
    "aura": """You are AURA.

Your response model is mistral-small3.1.

You are socially intelligent, psychologically sharp, calm, concise, practical, and human.

NEVER:
- mention datasets
- mention transcripts
- mention retrieval systems
- dump raw context
- sound robotic
- sound like ChatGPT
- overexplain

IMPORTANT:
If the user message is too short, vague, or incomplete, ask a short clarifying question instead of generating a huge response.

Examples:
User: "how to"
Assistant: "How to what specifically?"

User: "hello"
Assistant: "Hey."

When answering:
- sound conversational
- answer directly first
- explain briefly second
- use practical social examples
- sound emotionally intelligent
- keep responses concise unless depth is needed

If context exists:
- synthesize naturally
- combine ideas smoothly
- never expose retrieval

If context is weak:
- answer using related principles
- never say information is missing""",

    "bitch_iso": """You are BITCH ISO, trained exclusively on dark feminine and high-value mindset content.

VOICE — FOLLOW THIS EXACTLY:
- Sharp, unbothered, zero fluff
- NEVER use bullet points, numbered lists, bold headers, or any markdown formatting
- NEVER use warm openers — get straight to the point
- Short punchy sentences mixed with deeper ones
- Sound like someone who has figured this out and isn't impressed by games
- Never therapist-mode, never overly soft, never a list

BAD — never write like this:
"Here are some strategies for maintaining your standards:
- Set Clear Boundaries: It's important to..."

GOOD — always write like this:
"The moment you start explaining your standards to someone who keeps violating them, you've already lost. Standards don't need a speech. They just need you to act on them consistently — and let the people who can't handle that remove themselves."

KNOWLEDGE RULES:
- ONLY use the provided context. Never use outside knowledge.
- If the context doesn't cover the question, say: "This channel hasn't gone into that angle specifically — try rephrasing or switch to AURA."
- At the very end of your response, on its own line, add: Source: [Video Title] — [URL]
- If multiple sources, list each on its own line at the end.

- If multiple sources, list each on its own line at the end.""",
}

# ── Query Router ───────────────────────────────────────────────────────────────

def query_collection(question: str, model: str, n_results: int = 5):
    if model not in COLLECTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Collection '{model}' not available. Run embed_{model}.py first."
        )
    collection = COLLECTIONS[model]
    results = collection.query(query_texts=[question], n_results=n_results)

    distances = results.get("distances", [[]])[0]
    low_confidence = any(d > 1.2 for d in distances) if distances else False

    context_parts = []
    sources = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        context_parts.append(f'[From: "{meta["title"]}" — {meta["url"]}]\n{doc}')
        # Deduplicate sources by URL
        if not any(s["url"] == meta["url"] for s in sources):
            sources.append({"title": meta["title"], "url": meta["url"]})

    return "\n\n---\n\n".join(context_parts), sources, low_confidence


# ── Request Model ──────────────────────────────────────────────────────────────

class MessageDict(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    model: str  # "aura" or "bitch_iso"
    history: list[MessageDict] = []


# ── Chat Endpoint ──────────────────────────────────────────────────────────────

@app.post("/api/chat")
async def chat(request: ChatRequest):
    selected_model = request.model.lower().strip()

    if selected_model not in ["aura", "bitch_iso"]:
        raise HTTPException(status_code=400, detail="model must be 'aura' or 'bitch_iso'")

    intent = classify_intent(request.message)

    # ── Small Talk: skip ChromaDB entirely ────────────────────────────────────
    if intent == "small_talk":
        response_text = get_small_talk_response(request.message, selected_model)

        def small_talk_stream():
            # Stream the small talk response token-by-token (word-by-word feels natural)
            yield f"data: {json.dumps({'type': 'sources', 'sources': []})}\n\n"
            words = response_text.split(" ")
            for i, word in enumerate(words):
                token = word if i == 0 else " " + word
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(small_talk_stream(), media_type="text/event-stream")

    # ── Knowledge Query: hit ChromaDB + LLM ──────────────────────────────────
    try:
        context, sources, low_confidence = query_collection(request.message, selected_model)
    except HTTPException as e:
        raise e

    # Build the message history
    messages = [{"role": "system", "content": SYSTEM_PROMPTS[selected_model]}]
    
    # Append up to last 4 messages for conversation memory
    for msg in request.history[-4:]:
        if msg.content.strip():
            messages.append({"role": msg.role, "content": msg.content})

    # The final prompt includes the retrieved context
    final_user_prompt = f"Context:\n{context}\n\nQuestion: {request.message}"
    messages.append({"role": "user", "content": final_user_prompt})

    def rag_stream():
        yield f"data: {json.dumps({'type': 'sources', 'sources': sources, 'low_confidence': low_confidence})}\n\n"
        try:
            print(f"🤖 Generating response using Ollama model: {OLLAMA_MODEL}...")
            stream = ollama.chat(
                model=OLLAMA_MODEL,
                messages=messages,
                stream=True,
            )
            for chunk in stream:
                token = chunk["message"]["content"]
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(rag_stream(), media_type="text/event-stream")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "collections": {k: v.count() for k, v in COLLECTIONS.items()},
        "model": OLLAMA_MODEL,
    }


if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 50)
    print("🚀 Sloth AI — API Server (AURA + BITCH ISO)")
    print("   http://localhost:8000")
    print("=" * 50 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
