# ⚡ Nikola Tesla Digital Twin

> *"The present is theirs; the future, for which I have really worked, is mine."* — Nikola Tesla

A voice-interactive AI agent that **speaks, thinks, and answers as Nikola Tesla** — powered by a full RAG pipeline, long-term memory, and real-time voice cloning.

---

## 🏗️ Architecture Overview

```
User (Voice / Text)
        │
        ▼
┌───────────────────┐
│   Gradio UI       │  ← app.py  (Voice + Text interface)
│  (app.py)         │
└────────┬──────────┘
         │  LangGraph State Machine
         ▼
┌────────────────────────────────────────────────┐
│               AGENT GRAPH (graph.py)           │
│                                                │
│  [Gatekeeper] → [Memory] → [Librarian] → [Synthesizer] │
└────────────────────────────────────────────────┘
         │              │            │
         ▼              ▼            ▼
  SQLite (tesla.db)  Qdrant DB   Gemini 2.5 Flash
  (user facts)       (vectors)   (Tesla persona)
```

---

## 🧠 RAG Pipeline

### Phase 1 — Indexing (run once via `setup.py`)

| Step | Script | Description |
|------|--------|-------------|
| 1 | `databases.py` | Initialize SQLite + Qdrant |
| 2 | `pdf_parser.py` | Extract raw text from PDFs via PyMuPDF |
| 3 | `chapter_detector.py` | Group pages into structured chapters |
| 4 | `chunker.py` | Sliding-window chunking (4000 chars, 200 overlap) |
| 5 | `enricher.py` | Local AI metadata extraction (Ollama + Qwen 2.5 3B) |
| 6 | `vectorizer.py` | Embed chunks with `gemini-embedding-2`, inject into Qdrant |

### Phase 2 — Retrieval (every query)

```
User Query
    │
    ├─► [Timeline Agent]  SQL lookup if year detected (e.g. "what happened in 1893?")
    │
    └─► [Librarian RAG]
            │
            ├─ 1. Query Expansion  (Gemini 2.5 Flash rewrites query)
            ├─ 2. Embedding        (gemini-embedding-2 → 3072-dim vector)
            ├─ 3. ANN Search       (Qdrant cosine similarity, top-15 candidates)
            └─ 4. Cross-Encoder Reranking (ms-marco-MiniLM-L-6-v2, top-3 final)
```

### Phase 3 — Generation

```
[Retrieved Context] + [User Memory] + [Conversation History]
                        │
                        ▼
                Gemini 2.5 Flash
            (system-prompted as Tesla)
                        │
                        ▼
               Tesla's response (50-80 words)
                        │
                        ▼
              F5-TTS voice cloning → WAV audio
```

---

## 🔧 Tech Stack

| Component | Technology |
|-----------|------------|
| LLM | Google Gemini 2.5 Flash |
| Embeddings | `gemini-embedding-2` (3072-dim) |
| Agent Framework | LangGraph |
| Vector Store | Qdrant (local, file-based) |
| Relational DB | SQLite |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| Metadata Enrichment | Ollama (Qwen 2.5 3B, local) |
| Speech-to-Text | Gemini 2.5 Flash (audio input) |
| Text-to-Speech | F5-TTS (voice cloning) |
| UI | Gradio 6.0 |
| PDF Parsing | PyMuPDF (fitz) |

---

## 🚀 Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/Deepanshu-Nain/Nikola-Tesla-Digital-Twin.git
cd Nikola-Tesla-Digital-Twin
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

> **GPU strongly recommended** — F5-TTS voice cloning is very slow on CPU.

### 3. Set up environment variables

```bash
cp .env.sample .env
# Edit .env and fill in your Gemini API keys
```

```env
GEMINI_API_KEY_1=your_key_here
GEMINI_API_KEY_2=your_key_here   # optional — for round-robin rate limit bypass
GEMINI_API_KEY_3=your_key_here   # optional
```

### 4. Add source documents

Place Tesla's PDF documents inside `data/raw/`:
- *My Inventions* (Tesla's autobiography) — primary knowledge source
- Any other Tesla-related PDFs you want indexed

### 5. Add Tesla reference voice

Place a clean Tesla voice recording at:
```
data/raw_audio/tesla_reference.wav
```
If you only have an MP3, convert it first:
```bash
python src/convert_audio.py
```

### 6. Build the knowledge base (one-time)

```bash
python setup.py
```

This runs the full indexing pipeline (~5-15 min depending on chunk count and API rate limits).

> **Requirement:** [Ollama](https://ollama.ai/) must be running locally with `qwen2.5:3b` pulled:
> ```bash
> ollama pull qwen2.5:3b
> ```

### 7. Launch the Digital Twin

```bash
python src/app.py
```

Open `http://127.0.0.1:7860` in your browser.

---

## 📁 Project Structure

```
tesla-twin/
├── .env.sample              # Environment variable template
├── .gitignore
├── requirements.txt
├── setup.py                 # One-click indexing pipeline runner
│
├── data/
│   ├── raw/                 # Input PDFs (not committed)
│   ├── raw_audio/           # Tesla reference voice WAV
│   ├── processed/           # Intermediate JSON files (generated)
│   ├── audio_outputs/       # TTS output WAVs (generated at runtime)
│   └── models/              # Local ONNX models (not committed, too large)
│
├── db/
│   ├── tesla.db             # SQLite — user memory (generated)
│   └── qdrant/              # Qdrant vector store (generated)
│
└── src/
    ├── app.py               # Main Gradio UI + voice pipeline
    ├── api_manager.py       # Round-robin Gemini API key pool
    ├── convert_audio.py     # MP3 → WAV conversion utility
    │
    ├── agents/
    │   └── graph.py         # LangGraph state machine
    │
    ├── ingest/              # One-time indexing pipeline
    │   ├── databases.py     # DB initialization
    │   ├── pdf_parser.py    # PyMuPDF text extraction
    │   ├── chapter_detector.py  # Chapter grouping
    │   ├── chunker.py       # Sliding-window chunking
    │   ├── enricher.py      # Local AI metadata extraction
    │   └── vectorizer.py    # Embedding + Qdrant injection
    │
    ├── rag/
    │   ├── librarian.py     # Query expansion → ANN search → reranking
    │   └── timeline_agent.py  # SQL year-based lookup
    │
    ├── memory/
    │   └── memory_manager.py  # User long-term memory (SQLite)
    │
    ├── persona/
    │   └── tesla_brain.py   # Tesla system prompt + LLM generation
    │
    └── audio/
        └── voice_generator.py  # F5-TTS voice cloning
```

---

## 🔑 API Keys

This project uses **Google Gemini**. You can register multiple keys to bypass the free-tier rate limits (the `api_manager.py` rotates them automatically):

- Get keys at: https://aistudio.google.com/
- Add them to your `.env` as `GEMINI_API_KEY_1`, `GEMINI_API_KEY_2`, etc.

---

## 📝 Author

**Deepanshu Nain** — Roll No: 25/B01/045

---

## ⚠️ Notes

- The `data/` and `db/` directories (processed data, vector store, audio outputs) are **not committed** — they are generated by running `setup.py`.
- Large model files (`*.onnx`, `*.bin`) are also excluded.
- The reference voice audio is not committed; provide your own.
