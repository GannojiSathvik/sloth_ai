"""
STEP 5: Backend API for Fine-Tuned Model
Run this to serve your model with an API
Install: pip install fastapi uvicorn ollama
Run: uvicorn 4_backend_api:app --reload
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import ollama
import json
from pathlib import Path
from typing import Optional

app = FastAPI(
    title="Expert Advisor API",
    description="Ask questions and get expert advice based on fine-tuned model",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
MODEL_NAME = "llama3.1:8b"  # Change if using different model
SYSTEM_PROMPT = """You are an expert advisor providing thoughtful, helpful guidance.
Base your answers on the knowledge provided to you.
Be concise but comprehensive. Provide actionable advice when relevant."""

# Load training context
TRAINING_DATA = []
try:
    with open('training_data.json', 'r', encoding='utf-8') as f:
        TRAINING_DATA = json.load(f)
    print(f"✅ Loaded {len(TRAINING_DATA)} training samples as context")
except FileNotFoundError:
    print("⚠️  training_data.json not found. Model will work but without specific context.")

# Request/Response Models
class QueryRequest(BaseModel):
    question: str
    include_context: Optional[bool] = True

class QueryResponse(BaseModel):
    question: str
    answer: str
    confidence: float
    model: str
    context_used: int

class HealthResponse(BaseModel):
    status: str
    model: str
    trained_samples: int

def find_relevant_context(question: str, num_samples: int = 3) -> str:
    """
    Find training samples relevant to the question.
    In production, use semantic search (embeddings).
    For now, use simple keyword matching.
    """
    if not TRAINING_DATA:
        return ""
    
    question_words = set(question.lower().split())
    scores = []
    
    for i, sample in enumerate(TRAINING_DATA):
        input_words = set(sample['input'].lower().split())
        # Calculate overlap score
        overlap = len(question_words & input_words)
        if overlap > 0:
            scores.append((i, overlap))
    
    # Sort by overlap and get top samples
    scores.sort(key=lambda x: x[1], reverse=True)
    
    context_samples = []
    for idx, _ in scores[:num_samples]:
        context_samples.append(TRAINING_DATA[idx]['input'])
    
    return "\n---\n".join(context_samples) if context_samples else ""

def build_prompt(question: str, include_context: bool = True) -> str:
    """Build the full prompt for the model"""
    
    if include_context and TRAINING_DATA:
        context = find_relevant_context(question)
        if context:
            return f"""{SYSTEM_PROMPT}

Related Knowledge Base:
{context}

User Question: {question}

Provide a helpful, expert answer based on the knowledge above:"""
    
    return f"""{SYSTEM_PROMPT}

User Question: {question}

Provide a helpful, expert answer:"""

def estimate_confidence(answer: str) -> float:
    """
    Estimate confidence score based on answer quality.
    In production, use proper metrics.
    """
    # Simple heuristics
    if not answer or len(answer) < 20:
        return 0.3
    
    if len(answer) < 50:
        return 0.6
    
    if len(answer) < 500:
        return 0.8
    
    return 0.85

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API health and model status"""
    return HealthResponse(
        status="healthy",
        model=MODEL_NAME,
        trained_samples=len(TRAINING_DATA)
    )

@app.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    """
    Ask a question to the expert advisor
    
    Args:
        question: Your question
        include_context: Whether to use training context (default: True)
    
    Returns:
        Question, Answer, and Confidence Score
    """
    
    # Validate input
    if not request.question or len(request.question) < 3:
        raise HTTPException(
            status_code=400,
            detail="Question must be at least 3 characters long"
        )
    
    try:
        # Build prompt
        prompt = build_prompt(request.question, request.include_context)
        
        # Get context samples count
        context_count = 0
        if request.include_context and TRAINING_DATA:
            context_count = len(find_relevant_context(request.question).split("---"))
        
        # Generate response
        print(f"\n📝 Query: {request.question}")
        print(f"🔍 Using {context_count} context samples")
        
        response = ollama.generate(
            model=MODEL_NAME,
            prompt=prompt,
            stream=False,
        )
        
        answer = response['response'].strip()
        confidence = estimate_confidence(answer)
        
        return QueryResponse(
            question=request.question,
            answer=answer,
            confidence=confidence,
            model=MODEL_NAME,
            context_used=context_count
        )
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating response: {str(e)}"
        )

@app.get("/models")
async def list_models():
    """List available local Ollama models"""
    try:
        models = ollama.list()
        return {
            "available_models": [m['name'] for m in models['models']],
            "current_model": MODEL_NAME
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing models: {str(e)}"
        )

@app.post("/test")
async def test_model():
    """Test model with sample questions"""
    test_queries = [
        "How do I improve my communication skills?",
        "What are signs of a healthy relationship?",
        "How should I handle rejection?",
    ]
    
    results = []
    for query in test_queries:
        try:
            response = await ask_question(QueryRequest(question=query))
            results.append({
                "question": response.question,
                "answer": response.answer[:200] + "...",  # Truncate for display
                "confidence": response.confidence
            })
        except Exception as e:
            results.append({
                "question": query,
                "error": str(e)
            })
    
    return {"test_results": results}

@app.get("/stats")
async def get_stats():
    """Get statistics about the training data"""
    if not TRAINING_DATA:
        return {
            "total_samples": 0,
            "message": "No training data loaded"
        }
    
    lengths = [len(s['input'].split()) for s in TRAINING_DATA]
    
    return {
        "total_samples": len(TRAINING_DATA),
        "average_words_per_sample": sum(lengths) // len(lengths),
        "total_training_words": sum(lengths),
        "min_sample_length": min(lengths),
        "max_sample_length": max(lengths),
    }

# Root endpoint
@app.get("/")
async def root():
    """API Documentation"""
    return {
        "name": "Expert Advisor API",
        "version": "1.0.0",
        "endpoints": {
            "GET /health": "Check API health",
            "POST /ask": "Ask a question",
            "GET /models": "List available models",
            "POST /test": "Test with sample questions",
            "GET /stats": "Get training data statistics",
            "GET /docs": "Interactive API documentation (Swagger UI)",
        },
        "example_request": {
            "method": "POST",
            "url": "/ask",
            "body": {
                "question": "How do I improve my communication?",
                "include_context": True
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("🚀 EXPERT ADVISOR API")
    print("="*60)
    print(f"Model: {MODEL_NAME}")
    print(f"Training samples loaded: {len(TRAINING_DATA)}")
    print("\nAPI will start on: http://localhost:8000")
    print("Interactive docs: http://localhost:8000/docs")
    print("="*60 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )
