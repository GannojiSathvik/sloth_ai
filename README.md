# 🎯 Charisma on Command — YouTube RAG System

A **Retrieval-Augmented Generation (RAG)** pipeline that extracts every transcript from the [Charisma on Command](https://www.youtube.com/@Charismaoncommand) YouTube channel, embeds them into a local vector database, and lets you ask natural language questions answered exclusively from the channel's content.

---

## 🧠 How It Works

```
YouTube Channel (417 videos)
        │
        ▼  [Phase 1] youtube-transcript-api.py
    Transcripts saved to charisma_transcripts.json
        │
        ▼  [Phase 2] chuck_embeded.py
    Split into 500-char chunks → embedded as vectors → stored in ChromaDB
        │
        ▼  [Phase 3] query_prompt.py
    Your question → vector search → top 5 chunks → LLM answers with source attribution
```

### Why Vector Search?

When you ask *"How do I become more confident?"*, the system converts your question into a **vector** (list of numbers that captures its meaning). ChromaDB finds the 5 transcript chunks whose vectors are closest in meaning — even if they don't share the same words. The LLM then uses only those chunks to answer, always citing the source video and URL.

---

## 📁 Project Structure

```
rag_system/
├── youtube-transcript-api.py   # Phase 1: Extract transcripts from YouTube
├── chuck_embeded.py            # Phase 2: Chunk, embed, store in ChromaDB
├── query_prompt.py             # Phase 3: Query the RAG pipeline
├── charisma_transcripts.json   # Raw transcripts (gitignored, generated)
├── chroma_db/                  # Vector database (gitignored, generated)
└── cookies.txt                 # YouTube auth cookies (gitignored, sensitive)
```

---

## ⚙️ Setup

### 1. Clone the repo

```bash
git clone https://github.com/GannojiSathvik/sloth_ai.git
cd sloth_ai
```

### 2. Install dependencies

```bash
pip install yt-dlp youtube-transcript-api chromadb sentence-transformers langchain-text-splitters openai
```

### 3. Set your LLM API key (optional)

```bash
export OPENAI_API_KEY="sk-..."          # for GPT-4o-mini answers
# OR
export LLM_BACKEND=none                  # to see raw retrieved context (free)
# OR
export LLM_BACKEND=ollama                # to use local Llama3 via Ollama
```

---

## 🚀 Usage

### Phase 1 — Extract Transcripts

```bash
python youtube-transcript-api.py
```

- Uses your Chrome cookies to authenticate with YouTube (bypasses IP blocks)
- Saves all transcripts to `charisma_transcripts.json`
- **Incremental** — safe to stop and restart, already-fetched videos are skipped
- ~417 videos, takes 30–60 mins

> **Note:** macOS will ask for your login password to access Chrome's Keychain cookies. This is safe — it's a standard macOS security prompt.

### Phase 2 — Embed into ChromaDB

```bash
python chuck_embeded.py
```

- Splits each transcript into 500-character overlapping chunks
- Embeds chunks using `all-MiniLM-L6-v2` (runs locally, no API needed)
- Stores everything in `./chroma_db` with metadata
- **Incremental** — skips already-embedded chunks on re-run

### Phase 3 — Ask Questions

```bash
# Interactive mode
python query_prompt.py

# Single question
python query_prompt.py "How do I make a strong first impression?"
```

Example output:
```
📚 Retrieved Sources:
  1. [92.3%] 6 Habits That Kill Respect From Women
       https://youtube.com/watch?v=...
  2. [89.1%] How To Make Almost Anyone Like You
       https://youtube.com/watch?v=...

🤖 Answer:
According to the video "6 Habits That Kill Respect From Women"
(https://...), the key to a strong first impression is...
```

---

## 🔧 Configuration

| Variable | File | Default | Description |
|---|---|---|---|
| `CHANNEL_URL` | `youtube-transcript-api.py` | Charisma on Command | Target YouTube channel |
| `CHUNK_SIZE` | `chuck_embeded.py` | 500 chars | Size of each text chunk |
| `CHUNK_OVERLAP` | `chuck_embeded.py` | 50 chars | Overlap between chunks |
| `EMBED_MODEL` | `chuck_embeded.py` | `all-MiniLM-L6-v2` | Local sentence embedding model |
| `TOP_K` | `query_prompt.py` | 5 | Number of chunks retrieved per query |
| `LLM_BACKEND` | env var | `openai` | `openai` / `ollama` / `none` |

---

## 🚫 Troubleshooting: YouTube IP Blocks

YouTube aggressively blocks bulk transcript requests. Solutions in order of preference:

### Option 1 — Use a VPN (Recommended)
Connect to any VPN server → run the script → YouTube sees a fresh IP.
- [ProtonVPN](https://protonvpn.com) has a free tier that works perfectly

### Option 2 — Wait 4–6 hours
YouTube IP blocks are temporary. The script resumes from where it stopped.

### Option 3 — Use `cookies.txt` from browser
Install the Chrome extension **"Get cookies.txt LOCALLY"** → export → save as `cookies.txt` in the project folder.

### Why does VPN work?
YouTube doesn't block *users*, it blocks *IP addresses* that make too many requests too fast. A VPN gives you a **new IP address** that YouTube hasn't seen before → no block → requests go through.

---

## 🏗️ Architecture Details

### Embedding Model
Uses **`all-MiniLM-L6-v2`** from sentence-transformers:
- Runs **100% locally** — no API calls, no cost
- 384-dimensional vectors
- Downloads once (~80MB), then cached

### Vector Database
**ChromaDB** in persistent local mode:
- Stored in `./chroma_db/`
- Collection name: `charisma_on_command`
- Distance metric: cosine similarity
- Each chunk stored with metadata: `video_id`, `title`, `url`, `channel_name`

### Chunk Strategy
`RecursiveCharacterTextSplitter` with 500-char chunks and 50-char overlap:
- Splits on paragraph → sentence → word boundaries
- Overlap ensures context isn't lost at chunk boundaries
- Each chunk gets a deterministic MD5 ID for idempotent re-runs

---

## 📄 License

MIT License — feel free to adapt this pipeline for any YouTube channel.

---

## 🙏 Credits

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — YouTube extraction
- [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) — Transcript fetching
- [ChromaDB](https://www.trychroma.com) — Vector database
- [sentence-transformers](https://www.sbert.net) — Local embeddings
- [Charisma on Command](https://www.youtube.com/@Charismaoncommand) — Content source
