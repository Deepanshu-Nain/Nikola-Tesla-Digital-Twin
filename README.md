# ⚡ Nikola Tesla Digital Twin

> *"The present is theirs; the future, for which I have really worked, is mine."* — Nikola Tesla

A voice-interactive AI agent that **speaks, thinks, and answers as Nikola Tesla** — powered by a full RAG pipeline, long-term memory, and real-time voice cloning.

---

## 🚀 Quick Start (3 Steps for New Users)

The knowledge base is **pre-built and ships with this repo** — you do **not** need to re-index anything.

### Step 1 — Install dependencies

```bash
git clone https://github.com/Deepanshu-Nain/Nikola-Tesla-Digital-Twin.git
cd Nikola-Tesla-Digital-Twin
pip install -r requirements.txt
```

> **GPU strongly recommended** for F5-TTS voice synthesis. CPU works but is very slow.  
> GPU users — install PyTorch with CUDA first:
> ```bash
> pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
> pip install -r requirements.txt
> ```

### Step 2 — Configure your API keys

```bash
# Mac/Linux
cp .env.sample .env

# Windows
copy .env.sample .env
```

Open `.env` and add your **Google Gemini API key(s)** (free at [aistudio.google.com](https://aistudio.google.com)):

```env
GEMINI_API_KEY_1=your_real_key_here
GEMINI_API_KEY_2=optional_second_key   # helps bypass rate limits
GEMINI_API_KEY_3=optional_third_key
```

### Step 3 — Add Tesla's reference voice & launch

Place a clean Tesla voice WAV at `data/raw_audio/tesla_reference.wav`  
*(or convert from MP3: `python src/convert_audio.py`)*

Then validate your setup and launch:

```bash
python setup.py       # checks env + databases + voice file
python src/app.py     # starts the Gradio UI
```

Open **http://127.0.0.1:7860** and start talking to Tesla. ⚡

---

## 🏗️ Architecture Overview

```
User (Voice / Text)
        │
        ▼
┌───────────────────┐
│   Gradio UI       │  ← app.py  (Voice + Text interface)
└────────┬──────────┘
         │  LangGraph State Machine
         ▼
┌──────────────────────────────────────────────────────┐
│                  AGENT GRAPH  (graph.py)              │
│                                                       │
│  [Gatekeeper] → [Memory] → [Librarian] → [Synthesizer]│
└──────────────────────────────────────────────────────┘
         │              │            │
         ▼              ▼            ▼
  SQLite (tesla.db)  Qdrant DB   Gemini 2.5 Flash
  (user memory)      (vectors)   (Tesla persona)
```

---

## 🧠 RAG Pipeline

### Phase 1 — Indexing (already done — databases ship with repo)

| Step | Script | Description |
|------|--------|-------------|
| 1 | `databases.py` | Initialize SQLite + Qdrant |
| 2 | `pdf_parser.py` | Extract raw text from PDFs via PyMuPDF |
| 3 | `chapter_detector.py` | Group pages into chapters |
| 4 | `chunker.py` | Sliding-window chunking (4 000 chars, 200 overlap) |
| 5 | `enricher.py` | Local AI metadata extraction (Ollama + Qwen 2.5 3B) |
| 6 | `vectorizer.py` | Embed with `gemini-embedding-2` → inject into Qdrant |

### Phase 2 — Retrieval (every query)

```
User Query
    │
    ├─► [Timeline Agent]  SQL exact-year lookup (e.g. "what happened in 1893?")
    │
    └─► [Librarian RAG]
            │
            ├─ 1. Query Expansion  (Gemini rewrites query for better recall)
            ├─ 2. Embedding        (gemini-embedding-2 → 3072-dim vector)
            ├─ 3. ANN Search       (Qdrant cosine, top-15 candidates)
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
              50-80 word Tesla response
                        │
                        ▼
              F5-TTS voice cloning → WAV
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

## 📁 Project Structure

```
tesla-twin/
├── .env.sample              # Environment variable template (copy → .env)
├── .gitignore
├── requirements.txt
├── setup.py                 # Smart validator & rebuild orchestrator
│
├── data/
│   ├── raw/                 # Put your PDFs here (not committed)
│   ├── raw_audio/           # Tesla reference voice WAV (add manually)
│   ├── processed/           # Intermediate JSON — generated, not committed
│   ├── audio_outputs/       # TTS output WAVs — generated at runtime
│   └── models/              # Local ONNX models — not committed (too large)
│
├── db/                      # ✅ PRE-BUILT — ships with repo
│   ├── tesla.db             # SQLite (user memory + timeline)
│   └── qdrant/              # Qdrant vector store (Tesla knowledge base)
│
└── src/
    ├── app.py               # Main Gradio UI + voice pipeline
    ├── api_manager.py       # Round-robin Gemini API key pool
    ├── convert_audio.py     # MP3 → WAV conversion utility
    │
    ├── agents/
    │   └── graph.py         # LangGraph state machine (4 nodes)
    │
    ├── ingest/              # Indexing pipeline (already run — for reference)
    │   ├── databases.py
    │   ├── pdf_parser.py
    │   ├── chapter_detector.py
    │   ├── chunker.py
    │   ├── enricher.py
    │   └── vectorizer.py
    │
    ├── rag/
    │   ├── librarian.py     # Query expansion → ANN → reranking
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

## 🔄 Re-indexing with Custom Documents (Advanced)

Only needed if you want to add your own Tesla PDFs to the knowledge base:

1. Install [Ollama](https://ollama.ai/download) and pull the model:
   ```bash
   ollama pull qwen2.5:3b
   ```
2. Place your PDFs in `data/raw/`
3. Run the full rebuild:
   ```bash
   python setup.py --rebuild
   ```

---

## 🔑 API Keys

- Get free keys at: **https://aistudio.google.com/**
- Add multiple keys (`GEMINI_API_KEY_1`, `GEMINI_API_KEY_2`, ...) to rotate around free-tier rate limits automatically.

---

## 📝 Author

**Deepanshu Nain** — Roll No: 25/B01/045
