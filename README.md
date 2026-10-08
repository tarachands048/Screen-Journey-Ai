# Screen Journey

Turn screen recordings into structured, searchable, AI-powered memory.

---

## Prerequisites

Install these before running the app:

### 1. ffmpeg (required for video processing)
```
winget install ffmpeg
```
Or download from https://ffmpeg.org/download.html and add to PATH.

Verify: `ffmpeg -version`

### 2. Ollama (required for AI summaries and search)
Download and install from https://ollama.com

Then pull the required models:
```
ollama pull llama3.2
ollama pull nomic-embed-text
```

Verify Ollama is running: `ollama list`

### 3. Tesseract OCR (required for text extraction from frames)
Download installer from:
https://github.com/UB-Mannheim/tesseract/wiki

Install it (e.g., to `C:\Program Files\Tesseract-OCR\`).

Then update `backend/.env`:
```
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

Verify: `tesseract --version`

### 4. Python
**Recommended: Python 3.11 or 3.12** (some ML packages may not support Python 3.14 yet).

Check your version: `python --version`

If you have Python 3.14, you can still try — most packages will work but OCR may need Tesseract only.

---

## Setup

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Copy the example env file and edit it:
```bash
copy .env.example .env
# Edit .env and set TEAM_SECRET_TOKEN to a random value, e.g.:
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Start the backend:
```bash
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
copy .env.example .env.local
# Edit .env.local and set NEXT_PUBLIC_TEAM_TOKEN to the same value as TEAM_SECRET_TOKEN
npm run dev
```

Frontend runs at: http://localhost:3000
Backend API at: http://localhost:8000

---

## Usage

1. Open http://localhost:3000
2. Upload a screen recording (MP4 or MOV)
3. Enter a session name and click **Start Processing**
4. Watch the progress page — processing takes 1-10 min depending on video length
5. Once done, go to Dashboard to explore the navigation tree and chat

---

## Architecture

```
backend/
  main.py                  # FastAPI entry point
  models/                  # SQLAlchemy ORM + Pydantic schemas
  services/                # Processing pipeline components
    video_processor.py     # ffmpeg frame extraction
    change_detector.py     # OpenCV perceptual hash page detection
    ocr_service.py         # Tesseract OCR
    tree_builder.py        # Navigation tree construction
    scroll_deduplicator.py # Merge scrolled content
    summary_service.py     # Ollama LLM summaries
    embedding_service.py   # Ollama embeddings + ChromaDB
    chat_service.py        # RAG Q&A with Ollama
    sop_generator.py       # SOP document generation
    export_service.py      # Markdown/JSON export
  routers/                 # FastAPI route handlers
  tasks/
    processing_pipeline.py # Full pipeline (runs in background thread)
  storage/
    videos/                # Uploaded videos
    frames/                # Extracted frames

frontend/
  app/                     # Next.js 14 App Router pages
  components/              # Shared components
  lib/                     # API client, Zustand store, utils
  types/                   # TypeScript types
```

---

## Key Env Variables (`backend/.env`)

| Variable | Default | Description |
|---|---|---|
| `TEAM_SECRET_TOKEN` | *(required, no default)* | Shared auth token |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint |
| `OLLAMA_LLM_MODEL` | `llama3.2` | Model for summaries & Q&A |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Model for embeddings |
| `TESSERACT_CMD` | `tesseract` | Path to Tesseract binary |
| `STORAGE_PATH` | `./storage` | Where to store videos & frames |
| `PAGE_CHANGE_THRESHOLD` | `40` | Perceptual hash diff sensitivity |

---

## Troubleshooting

**"ffmpeg not found"** — Install ffmpeg and ensure it's in your PATH.

**"Ollama connection refused"** — Start Ollama (`ollama serve`) and ensure models are pulled.

**"Tesseract not found"** — Install Tesseract and set `TESSERACT_CMD` in `.env`.

**OCR returns empty text** — Tesseract may need language packs. Run: `tesseract --list-langs`

**ChromaDB errors** — Delete the `backend/chroma_store/` folder and restart.

**Python compatibility** — If you see torch/easyocr errors, you're likely on Python 3.14. Use Python 3.11 or 3.12.
