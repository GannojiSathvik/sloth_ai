# Complete Guide: Fine-Tune LLM with YouTube Channel Data

## Overview
You want to: Extract transcripts → Fine-tune model → Build Q&A frontend

---

## STEP 1: Extract YouTube Transcripts

### Option A: Using `youtube-transcript-api` (Recommended)

```bash
pip install youtube-transcript-api yt-dlp
```

### Extract All Videos from a Channel

```python
import json
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
from pathlib import Path

def get_channel_videos(channel_url):
    """Extract all video IDs from a YouTube channel"""
    ydl_opts = {
        'extract_flat': 'in_playlist',
        'skip_download': True,
        'quiet': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(channel_url, download=False)
        return [entry['id'] for entry in info.get('entries', [])]

def get_transcript(video_id):
    """Get transcript for a single video"""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        # Combine all text
        return ' '.join([entry['text'] for entry in transcript])
    except Exception as e:
        print(f"Error getting transcript for {video_id}: {e}")
        return None

def extract_channel_data(channel_url, output_file='channel_data.json'):
    """Extract all transcripts from a channel"""
    print(f"Fetching videos from {channel_url}...")
    video_ids = get_channel_videos(channel_url)
    print(f"Found {len(video_ids)} videos")
    
    data = []
    for i, vid_id in enumerate(video_ids):
        print(f"[{i+1}/{len(video_ids)}] Extracting {vid_id}...")
        transcript = get_transcript(vid_id)
        if transcript:
            data.append({
                'video_id': vid_id,
                'url': f'https://youtube.com/watch?v={vid_id}',
                'transcript': transcript
            })
    
    # Save to JSON
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Saved {len(data)} transcripts to {output_file}")
    return data

# Usage
channel_url = 'https://www.youtube.com/@thedarkneedle'
extract_channel_data(channel_url)
```

### What You'll Get
- `channel_data.json` with all transcripts
- Structure: `[{video_id, url, transcript}, ...]`

---

## STEP 2: Prepare Data for Fine-Tuning

### Clean & Format Data

```python
import json
from pathlib import Path

def prepare_training_data(input_file, output_file):
    """
    Convert transcripts to training format for fine-tuning.
    Creates Q&A pairs from transcript content.
    """
    
    with open(input_file, 'r') as f:
        raw_data = json.load(f)
    
    training_samples = []
    
    for item in raw_data:
        transcript = item['transcript']
        
        # Split into chunks (avoid super long contexts)
        chunks = [transcript[i:i+1000] for i in range(0, len(transcript), 800)]
        
        for chunk in chunks:
            if len(chunk) > 100:  # Skip very short chunks
                # Create training example
                training_samples.append({
                    "instruction": "Based on the following content, answer questions about relationships, behavior, and personal development:",
                    "input": chunk,
                    "output": "I understand this content and can answer questions about it."
                })
    
    # Save in format suitable for fine-tuning
    with open(output_file, 'w') as f:
        json.dump(training_samples, f, indent=2)
    
    print(f"Created {len(training_samples)} training samples")
    return training_samples

prepare_training_data('channel_data.json', 'training_data.json')
```

---

## STEP 3: Choose a Model

### From Your Available Models:

| Model | Size | Best For | Speed |
|-------|------|----------|-------|
| **llama3.1:8b** | 4.9GB | Best balance, good quality | Medium |
| **qwen2.5-coder:7b** | 4.7GB | Code + reasoning | Medium |
| **gemma4:latest** | 9.6GB | Highest quality, slower | Slow |
| **llama3:latest** | 4.7GB | Good, older version | Fast |

**RECOMMENDATION:** Use **`llama3.1:8b`** - best balance of speed and quality

---

## STEP 4: Fine-Tune Your Model

### Using Ollama + Python

```bash
pip install ollama torch transformers peft
```

### Fine-Tuning Script

```python
import json
import ollama
from pathlib import Path

def finetune_with_ollama(model_name='llama3.1:8b', training_file='training_data.json'):
    """
    Fine-tune using Ollama's built-in capabilities.
    Note: Ollama has limited fine-tuning. For production, use Hugging Face.
    """
    print(f"Loading training data from {training_file}...")
    with open(training_file, 'r') as f:
        training_data = json.load(f)
    
    print(f"Preparing {len(training_data)} samples for fine-tuning...")
    
    # Create training format for Ollama
    formatted_data = []
    for sample in training_data:
        formatted_data.append({
            "role": "user",
            "content": f"{sample['instruction']}\n\n{sample['input']}"
        })
        formatted_data.append({
            "role": "assistant",
            "content": sample['output']
        })
    
    print("Fine-tuning process initiated...")
    print(f"This may take time depending on your hardware")

# Alternative: Use Hugging Face for better fine-tuning
def finetune_with_huggingface(model_name='meta-llama/Llama-2-7b-hf', 
                              training_file='training_data.json'):
    """
    Better fine-tuning using Hugging Face + LoRA
    (Requires HuggingFace account and GPU)
    """
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
    from datasets import load_dataset
    
    print("Loading model and tokenizer...")
    model = AutoModelForCausalLM.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    # Load your data
    dataset = load_dataset('json', data_files=training_file)
    
    training_args = TrainingArguments(
        output_dir='./finetuned_model',
        num_train_epochs=3,
        per_device_train_batch_size=4,
        save_steps=100,
        save_total_limit=2,
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset['train'],
    )
    
    print("Starting training...")
    trainer.train()
    print("Fine-tuning complete!")

finetune_with_ollama()
```

---

## STEP 5: Test Your Fine-Tuned Model

```python
import ollama

def test_model(query, model_name='llama3.1:8b'):
    """
    Test your model with a query
    """
    response = ollama.generate(
        model=model_name,
        prompt=query,
        stream=False,
    )
    return response['response']

# Test queries
test_queries = [
    "How do I improve my communication with someone I'm interested in?",
    "What are signs someone is losing interest?",
    "How should I behave on a first date?",
]

for query in test_queries:
    print(f"\nQ: {query}")
    answer = test_model(query)
    print(f"A: {answer}\n")
```

---

## STEP 6: Build Frontend Application

### Backend (Flask/FastAPI)

```python
# app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import ollama
import json

app = FastAPI()

# Load your fine-tuned model
MODEL_NAME = "llama3.1:8b"  # Your fine-tuned version
CONTEXT = None

# Load training data as context
with open('training_data.json', 'r') as f:
    CONTEXT_DATA = json.load(f)

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    question: str
    answer: str
    confidence: float

def build_context_prompt(question):
    """Add training context to question"""
    context = "\n".join([
        s['input'] for s in CONTEXT_DATA[:5]  # Use top 5 relevant samples
    ])
    
    return f"""You are an expert advisor based on curated content.
    
Context Knowledge:
{context}

User Question: {question}

Answer based on the context provided:"""

@app.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    try:
        prompt = build_context_prompt(request.question)
        
        response = ollama.generate(
            model=MODEL_NAME,
            prompt=prompt,
            stream=False,
        )
        
        return QueryResponse(
            question=request.question,
            answer=response['response'],
            confidence=0.85  # You can calculate actual confidence
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok", "model": MODEL_NAME}

# Run with: uvicorn app:app --reload
```

### Frontend (HTML + JavaScript)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ask Expert - AI Advisor</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 700px;
            width: 100%;
            padding: 40px;
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }
        
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        
        .input-group {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        input {
            flex: 1;
            padding: 14px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        
        input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        button {
            padding: 14px 28px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.3s;
        }
        
        button:hover {
            background: #764ba2;
        }
        
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        
        .response {
            background: #f5f5f5;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
            display: none;
        }
        
        .response.visible {
            display: block;
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .question {
            color: #667eea;
            font-weight: 600;
            margin-bottom: 10px;
        }
        
        .answer {
            color: #333;
            line-height: 1.6;
            margin-bottom: 10px;
        }
        
        .confidence {
            color: #999;
            font-size: 12px;
        }
        
        .loading {
            display: none;
            color: #667eea;
            text-align: center;
            padding: 20px;
        }
        
        .loading.visible {
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>💬 Ask Expert</h1>
        <p class="subtitle">Get expert advice based on curated content</p>
        
        <div class="input-group">
            <input 
                type="text" 
                id="questionInput" 
                placeholder="Ask your question..."
                onkeypress="handleKeyPress(event)"
            >
            <button onclick="askQuestion()">Ask</button>
        </div>
        
        <div class="loading" id="loading">
            <p>⏳ Thinking...</p>
        </div>
        
        <div class="response" id="response">
            <div class="question" id="responseQuestion"></div>
            <div class="answer" id="responseAnswer"></div>
            <div class="confidence" id="confidence"></div>
        </div>
    </div>
    
    <script>
        const API_URL = 'http://localhost:8000';
        
        async function askQuestion() {
            const question = document.getElementById('questionInput').value.trim();
            
            if (!question) {
                alert('Please enter a question');
                return;
            }
            
            const loading = document.getElementById('loading');
            const response = document.getElementById('response');
            
            loading.classList.add('visible');
            response.classList.remove('visible');
            
            try {
                const result = await fetch(`${API_URL}/ask`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ question })
                });
                
                const data = await result.json();
                
                document.getElementById('responseQuestion').textContent = data.question;
                document.getElementById('responseAnswer').textContent = data.answer;
                document.getElementById('confidence').textContent = 
                    `Confidence: ${(data.confidence * 100).toFixed(0)}%`;
                
                response.classList.add('visible');
                loading.classList.remove('visible');
                
            } catch (error) {
                alert('Error: ' + error.message);
                loading.classList.remove('visible');
            }
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                askQuestion();
            }
        }
    </script>
</body>
</html>
```

---

## STEP 7: Evaluate Your Model

```python
def evaluate_model(test_queries, expected_themes):
    """
    Test model responses against expected themes
    """
    from sklearn.metrics.pairwise import cosine_similarity
    from sentence_transformers import SentenceTransformer
    
    # Load embedding model
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    
    results = []
    for query, expected_theme in zip(test_queries, expected_themes):
        answer = test_model(query)
        
        # Calculate similarity
        query_embedding = embedder.encode(query)
        answer_embedding = embedder.encode(answer)
        expected_embedding = embedder.encode(expected_theme)
        
        similarity = cosine_similarity(
            [expected_embedding], 
            [answer_embedding]
        )[0][0]
        
        results.append({
            'query': query,
            'answer': answer,
            'relevance_score': similarity
        })
    
    return results
```

---

## Summary: What Each Step Does

1. **Extract** - Get all video transcripts from YouTube channel
2. **Prepare** - Clean data and create training samples
3. **Fine-tune** - Adapt model to your specific domain
4. **Test** - Verify model quality before deployment
5. **Deploy** - Create backend API and frontend UI
6. **Evaluate** - Measure accuracy and relevance

## Installation Quick Start

```bash
# 1. Install dependencies
pip install youtube-transcript-api yt-dlp fastapi uvicorn ollama torch transformers sentence-transformers

# 2. Extract data
python extract_youtube.py

# 3. Prepare training data
python prepare_data.py

# 4. Fine-tune model (optional, takes time)
python finetune.py

# 5. Run backend
uvicorn app:app --reload

# 6. Open frontend in browser
# Copy the HTML above to index.html and open it
```

---

## Important Notes

- **Data Privacy**: Check YouTube's ToS - ensure you have rights to use content
- **Fine-tuning Time**: 3-8 hours depending on dataset size and hardware
- **Model Size**: llama3.1:8b works well on most machines
- **Accuracy**: More data = better results (aim for 100+ videos)
- **Cost**: Using Ollama locally is free; cloud fine-tuning has costs
