# Quick Start Guide - Build Your AI Expert Advisor

## What You're Building
A complete AI application that:
1. Extracts transcripts from a YouTube channel
2. Fine-tunes an LLM with that data
3. Serves an API
4. Provides a beautiful web interface

---

## 📋 Prerequisites

Make sure you have:
- Python 3.9+
- Ollama installed (download from https://ollama.ai)
- Terminal/Command prompt access

---

## 🚀 COMPLETE SETUP IN 5 STEPS

### Step 1: Install Dependencies (3 minutes)

**Mac/Linux:**
```bash
pip install youtube-transcript-api yt-dlp fastapi uvicorn ollama torch

# Also install optional but helpful
pip install sentence-transformers pydantic
```

**Windows (Command Prompt):**
```bash
pip install youtube-transcript-api yt-dlp fastapi uvicorn ollama torch
```

**Verify Ollama is running:**
```bash
# In a separate terminal, check if Ollama is running
ollama list

# If no models show up, download one:
ollama pull llama3.1:8b
```

---

### Step 2: Extract YouTube Transcripts (5-15 minutes)

**This will download all transcripts from a YouTube channel**

```bash
# Navigate to where you saved the scripts
cd /path/to/scripts

# Run extraction
python 1_extract_youtube_transcripts.py
```

**What happens:**
- Downloads all video IDs from the channel
- Extracts transcripts for each video
- Saves to `channel_data.json`
- Shows progress

**Expected output:**
```
============================================================
EXTRACTING YOUTUBE CHANNEL TRANSCRIPTS
============================================================

📺 Fetching videos from: https://www.youtube.com/@thedarkneedle
✅ Found 47 videos
[1/47] Extracting: youtube.com/watch?v=abc123...
...
============================================================
✅ EXTRACTION COMPLETE
============================================================
Total videos: 47
Transcripts extracted: 45
Success rate: 95.7%
```

---

### Step 3: Prepare Training Data (2-5 minutes)

**Converts raw transcripts into training format**

```bash
python 2_prepare_training_data.py
```

**What happens:**
- Cleans and splits transcripts
- Creates training samples
- Validates data quality
- Saves to `training_data.json`

**Expected output:**
```
============================================================
TRAINING DATA PREPARATION PIPELINE
============================================================

1️⃣  Loading extracted transcript data...
✅ Loaded 45 transcripts

2️⃣  Creating training samples...
Created 1247 training samples

3️⃣  Saving training data...
✅ Saved 1247 training samples to training_data.json

4️⃣  Analyzing data quality...

============================================================
DATA ANALYSIS
============================================================
Total samples: 1247
Average words per sample: 182
Min words: 101
Max words: 498
Total training words: 226,854

Samples in ideal range (100-500 words): 1189
Quality score: 95.3%
```

---

### Step 4: Start the Backend API (Runs indefinitely)

**Keep this terminal open while you use the app**

```bash
# Still in the same directory
python 4_backend_api.py
```

**Expected output:**
```
============================================================
🚀 EXPERT ADVISOR API
============================================================
Model: llama3.1:8b
Training samples loaded: 1247

API will start on: http://localhost:8000
Interactive docs: http://localhost:8000/docs
============================================================
```

**Important:**
- Keep this terminal open
- Don't close it while using the app
- If you see errors, check if Ollama is running

---

### Step 5: Open the Web Interface

**In your web browser, open this file:**

```
5_frontend.html
```

**Or copy the full path:**
```
file:///path/to/5_frontend.html
```

**The interface is ready to use!**

---

## ✅ Testing the Complete System

### 1. Check API Health

Visit in browser:
```
http://localhost:8000/docs
```

This shows interactive API documentation. You can:
- See all available endpoints
- Test the `/ask` endpoint
- Check `/health` status

### 2. Ask Your First Question

In the web interface, type:
```
How do I improve my communication skills?
```

Click "Ask" and wait for response.

### 3. Check Backend Logs

In the terminal running the API, you'll see:
```
📝 Query: How do I improve my communication skills?
🔍 Using 3 context samples
```

---

## 🎯 Understanding the Files

| File | Purpose | When to Run |
|------|---------|-----------|
| `1_extract_youtube_transcripts.py` | Download YouTube transcripts | Once per channel |
| `2_prepare_training_data.py` | Prepare data for training | After extraction |
| `4_backend_api.py` | Run the API server | Always (keep open) |
| `5_frontend.html` | Web interface | Open in browser |

---

## 📊 Example Workflow

```
Terminal 1 (Setup):
$ python 1_extract_youtube_transcripts.py     # Wait for completion
$ python 2_prepare_training_data.py           # Wait for completion
                                              
Terminal 2 (API Server):
$ python 4_backend_api.py                     # Keep open forever
                                              
Browser:
Open 5_frontend.html and start asking questions!
```

---

## ❓ Common Issues & Solutions

### "ModuleNotFoundError: No module named 'ollama'"
**Solution:**
```bash
pip install ollama
```

### "Connection refused - cannot connect to API"
**Solution:**
- Make sure `python 4_backend_api.py` is running
- Check that the terminal shows "API will start on: http://localhost:8000"
- Close and reopen the browser

### "No transcripts extracted"
**Solution:**
- Check the YouTube channel URL is correct
- The channel must have public transcripts
- Some videos may not have transcripts

### Ollama is very slow
**Solution:**
- Use a smaller model: `ollama pull llama2` (4GB instead of 8GB)
- Close other applications
- GPU acceleration helps (if available)

### "training_data.json not found"
**Solution:**
- Make sure you ran `2_prepare_training_data.py` AFTER `1_extract_youtube_transcripts.py`
- Both scripts must be in the same directory

---

## 🚀 Advanced: Customize Your Model

### Use a Different YouTube Channel

Edit `1_extract_youtube_transcripts.py`, line 67:
```python
CHANNEL_URL = "https://www.youtube.com/@yourchannelname"
```

Then re-run Step 2.

### Use a Different Ollama Model

Edit `4_backend_api.py`, line 16:
```python
MODEL_NAME = "gemma4:latest"  # Or "qwen2.5-coder:7b"
```

### Customize the System Prompt

Edit `4_backend_api.py`, line 18-20:
```python
SYSTEM_PROMPT = """Your custom instructions here..."""
```

---

## 📈 Performance Optimization

### Make it Faster
```python
# In 4_backend_api.py, line 16
MODEL_NAME = "llama3:latest"  # Smaller, faster
```

### Make it More Accurate
```python
# In 4_backend_api.py, line 16
MODEL_NAME = "gemma4:latest"  # Larger, slower but better
```

### Use GPU Acceleration
```bash
# Install GPU support (NVIDIA)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

---

## 📝 Next Steps

1. **Test with different channels** - Try extracting from multiple YouTube channels
2. **Add database** - Store conversation history
3. **Deploy online** - Use Heroku/AWS to make it publicly accessible
4. **Add RAG** - Implement semantic search for better context
5. **Fine-tune deeply** - Use Hugging Face for production-grade fine-tuning

---

## 🆘 Getting Help

If something breaks:

1. **Check terminal errors** - Read the error message carefully
2. **Verify prerequisites** - Make sure Ollama is running: `ollama list`
3. **Check file locations** - All scripts should be in same directory
4. **Restart API** - Kill and restart `4_backend_api.py`
5. **Clear browser cache** - Hard refresh: Ctrl+Shift+Delete (Windows) or Cmd+Shift+Delete (Mac)

---

## 📞 Quick Debugging

```bash
# Check if API is running
curl http://localhost:8000/health

# Check available models
curl http://localhost:8000/models

# Check training stats
curl http://localhost:8000/stats

# Test the model
curl http://localhost:8000/test
```

---

## ✨ You've Built a Complete AI Application!

Congratulations! You now have:
- ✅ YouTube transcript extraction
- ✅ Fine-tuned AI model
- ✅ REST API backend
- ✅ Beautiful web frontend
- ✅ Training context management
- ✅ Confidence scoring

**Your AI expert advisor is ready to answer questions based on any YouTube channel!**

---

## 💡 What to Do Next

- **Customize** the system prompt to change the AI's behavior
- **Add more channels** to the training data
- **Deploy** to cloud for public access
- **Add authentication** if you want to control access
- **Implement persistence** to save conversation history

Happy building! 🚀
