# Screen Journey Memory System — PROJECT.md
> Complete specification for Claude Code. Read this entire file before writing any code.

---

## 1. WHAT THIS PROJECT IS

A web application where a team uploads screen recordings and the system converts them into **structured, searchable, intelligent memory** of everything that happened on screen.

This is NOT:
- A video transcription tool
- A simple OCR tool
- A screen recorder
- A video summarizer

This IS:
- A structured navigation memory system
- A session journey organizer
- A team knowledge base from screen recordings
- A Q&A system over visual screen content

**Core tagline:** "Upload a screen recording and turn it into a searchable structured memory."

---

## 2. CORE PHILOSOPHY

The intelligence of this product comes from:
- Understanding **navigation flow**, not just extracting text
- Preserving **branching** (user went back, took different path)
- Understanding **page transitions** (new page, modal, tab switch)
- **Deduplicating** scrolled content (don't store navbar 40 times)
- Preserving **chronological context**
- Storing **structured relationships** between pages
- Enabling **intelligent retrieval** by meaning

The system thinks of a recording as:
```
SESSION
  → PAGES
      → STEPS
          → EVENTS
              → CONTENT
```

A recording is NOT linear only. It can branch:
```
Homepage
 ├── Pricing
 │     ├── Enterprise
 │     └── FAQ
 └── Features
```

---

## 3. TECH STACK

### Frontend
- **Framework:** Next.js 14 (App Router)
- **Styling:** Tailwind CSS + shadcn/ui
- **Theme:** Dark/Light both, system default, toggle in top right, persists in localStorage
- **Icons:** Lucide React
- **State:** Zustand
- **HTTP Client:** Axios

### Backend
- **Framework:** FastAPI (Python)
- **Task Queue:** Celery + Redis (for async video processing)
- **Server:** Uvicorn

### Processing Pipeline
- **Frame extraction:** ffmpeg + ffmpeg-python
- **Page change detection:** OpenCV (cv2) + imagehash
- **OCR:** EasyOCR (runs on CPU, better than Tesseract)
- **Sensitive content detection:** regex patterns (emails, passwords, credit cards)

### AI / LLM
- **Provider:** Anthropic API (Claude claude-sonnet-4-20250514)
- **Usage:** Summaries, Q&A, SOP generation
- **Embeddings:** sentence-transformers (`all-MiniLM-L6-v2`) — runs locally on CPU

### Storage
- **Structured data:** SQLite (via SQLAlchemy)
- **Vector search:** ChromaDB (local)
- **Files/frames:** Local filesystem under `/storage/`

### Auth
- Simple team token — one shared secret key stored in `.env`
- All routes protected by this token
- No user accounts needed for Phase 1

---

## 4. FOLDER STRUCTURE

```
screen-journey/
├── frontend/                        # Next.js app
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx                 # Landing / Upload
│   │   ├── processing/[id]/page.tsx # Processing status
│   │   ├── dashboard/page.tsx       # Main dashboard
│   │   ├── session/[id]/page.tsx    # Session detail view
│   │   ├── step/[id]/page.tsx       # Step detail view
│   │   ├── search/page.tsx          # Global search
│   │   ├── compare/page.tsx         # Branch comparison
│   │   └── export/[id]/page.tsx     # Export session
│   ├── components/
│   │   ├── ui/                      # shadcn components
│   │   ├── SessionList.tsx
│   │   ├── NavigationTree.tsx
│   │   ├── ChatPanel.tsx
│   │   ├── Timeline.tsx
│   │   ├── StepCard.tsx
│   │   ├── SearchResults.tsx
│   │   ├── CompareView.tsx
│   │   ├── StatsBar.tsx
│   │   ├── HeatmapTimeline.tsx
│   │   ├── AnnotationPanel.tsx
│   │   ├── TagManager.tsx
│   │   ├── BookmarkButton.tsx
│   │   └── ThemeToggle.tsx
│   ├── lib/
│   │   ├── api.ts                   # All API calls
│   │   ├── store.ts                 # Zustand store
│   │   └── utils.ts
│   ├── types/
│   │   └── index.ts                 # All TypeScript types
│   └── public/
│
├── backend/                         # FastAPI app
│   ├── main.py                      # App entry point
│   ├── routers/
│   │   ├── upload.py
│   │   ├── sessions.py
│   │   ├── steps.py
│   │   ├── chat.py
│   │   ├── search.py
│   │   ├── export.py
│   │   ├── annotations.py
│   │   ├── bookmarks.py
│   │   ├── tags.py
│   │   └── compare.py
│   ├── services/
│   │   ├── video_processor.py       # ffmpeg frame extraction
│   │   ├── change_detector.py       # OpenCV page change detection
│   │   ├── ocr_service.py           # EasyOCR text extraction
│   │   ├── tree_builder.py          # Navigation tree construction
│   │   ├── scroll_deduplicator.py   # Merge scrolled content
│   │   ├── summary_service.py       # Claude AI summaries
│   │   ├── embedding_service.py     # sentence-transformers
│   │   ├── chat_service.py          # Claude Q&A with RAG
│   │   ├── sop_generator.py         # SOP document generation
│   │   └── export_service.py        # Markdown/JSON export
│   ├── models/
│   │   ├── database.py              # SQLAlchemy setup
│   │   └── schemas.py               # All DB models + Pydantic schemas
│   ├── tasks/
│   │   └── celery_tasks.py          # Async processing tasks
│   ├── utils/
│   │   ├── auth.py                  # Token auth middleware
│   │   └── file_utils.py
│   ├── chroma_store/                # ChromaDB persistent storage
│   ├── storage/                     # Uploaded videos + extracted frames
│   │   ├── videos/
│   │   └── frames/
│   ├── database.db                  # SQLite database
│   ├── requirements.txt
│   └── .env
│
└── README.md
```

---

## 5. DATABASE SCHEMA (SQLite via SQLAlchemy)

```sql
-- Sessions table
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,               -- UUID
    name TEXT NOT NULL,
    description TEXT,
    video_path TEXT,
    status TEXT DEFAULT 'pending',     -- pending | processing | done | failed
    total_duration_seconds INTEGER,
    total_pages INTEGER DEFAULT 0,
    total_steps INTEGER DEFAULT 0,
    total_backtracks INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT NOW,
    processed_at DATETIME,
    folder_id TEXT REFERENCES folders(id)
);

-- Pages table
CREATE TABLE pages (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id),
    title TEXT,                        -- AI-inferred page title
    url_or_identifier TEXT,            -- if URL visible in OCR
    parent_page_id TEXT REFERENCES pages(id),  -- for tree structure
    depth INTEGER DEFAULT 0,           -- depth in navigation tree
    visit_count INTEGER DEFAULT 1,     -- if user returned to this page
    first_visited_at INTEGER,          -- timestamp in seconds from video start
    last_visited_at INTEGER,
    time_spent_seconds INTEGER,
    page_summary TEXT,                 -- AI summary
    sequence_order INTEGER             -- chronological order
);

-- Steps table (individual meaningful frames/states within a page)
CREATE TABLE steps (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id),
    page_id TEXT REFERENCES pages(id),
    step_type TEXT,                    -- page_load | scroll | modal_open | tab_switch | back_navigation | form_interaction
    screenshot_path TEXT,
    extracted_text TEXT,               -- full OCR text
    text_summary TEXT,                 -- AI summary of this step
    timestamp_start INTEGER,           -- seconds from video start
    timestamp_end INTEGER,
    ocr_confidence REAL,               -- avg OCR confidence score
    sequence_order INTEGER,
    is_backtrack BOOLEAN DEFAULT FALSE
);

-- Navigation events table
CREATE TABLE nav_events (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id),
    from_step_id TEXT REFERENCES steps(id),
    to_step_id TEXT REFERENCES steps(id),
    event_type TEXT,                   -- forward | back | new_tab | modal_open | modal_close
    timestamp INTEGER
);

-- Annotations table (team comments on any step)
CREATE TABLE annotations (
    id TEXT PRIMARY KEY,
    step_id TEXT REFERENCES steps(id),
    session_id TEXT REFERENCES sessions(id),
    author_name TEXT,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT NOW
);

-- Bookmarks table
CREATE TABLE bookmarks (
    id TEXT PRIMARY KEY,
    step_id TEXT REFERENCES steps(id),
    session_id TEXT REFERENCES sessions(id),
    label TEXT,
    created_at DATETIME DEFAULT NOW
);

-- Tags table
CREATE TABLE tags (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    color TEXT DEFAULT '#6366f1'
);

-- Session tags junction
CREATE TABLE session_tags (
    session_id TEXT REFERENCES sessions(id),
    tag_id TEXT REFERENCES tags(id),
    PRIMARY KEY (session_id, tag_id)
);

-- Folders table (organize sessions into projects)
CREATE TABLE folders (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    color TEXT DEFAULT '#6366f1',
    created_at DATETIME DEFAULT NOW
);

-- Chat history table
CREATE TABLE chat_messages (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id),
    role TEXT,                         -- user | assistant
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT NOW
);
```

---

## 6. SESSION TREE JSON STRUCTURE

This is the core data structure stored per session:

```json
{
  "session_id": "uuid",
  "name": "Product Demo Recording",
  "total_duration": 420,
  "tree": {
    "id": "page_001",
    "title": "Homepage",
    "depth": 0,
    "time_spent": 45,
    "timestamp_start": 0,
    "children": [
      {
        "id": "page_002",
        "title": "Pricing Page",
        "depth": 1,
        "time_spent": 80,
        "timestamp_start": 45,
        "is_backtrack_destination": false,
        "children": [
          {
            "id": "page_003",
            "title": "Enterprise Pricing",
            "depth": 2,
            "time_spent": 33,
            "timestamp_start": 125,
            "children": []
          },
          {
            "id": "page_004",
            "title": "FAQ",
            "depth": 2,
            "time_spent": 28,
            "timestamp_start": 165,
            "children": []
          }
        ]
      },
      {
        "id": "page_005",
        "title": "Features Page",
        "depth": 1,
        "time_spent": 120,
        "timestamp_start": 210,
        "children": []
      }
    ]
  },
  "timeline": [
    {"sequence": 1, "page_id": "page_001", "event": "page_load", "timestamp": 0},
    {"sequence": 2, "page_id": "page_002", "event": "forward", "timestamp": 45},
    {"sequence": 3, "page_id": "page_003", "event": "forward", "timestamp": 125},
    {"sequence": 4, "page_id": "page_002", "event": "back", "timestamp": 158},
    {"sequence": 5, "page_id": "page_004", "event": "forward", "timestamp": 165},
    {"sequence": 6, "page_id": "page_001", "event": "back", "timestamp": 193},
    {"sequence": 7, "page_id": "page_005", "event": "forward", "timestamp": 210}
  ]
}
```

---

## 7. ALL API ROUTES

### Upload
```
POST   /api/upload
       Body: multipart/form-data { video: File, name: string, description: string }
       Response: { session_id, status: "processing" }
```

### Sessions
```
GET    /api/sessions
       Response: [ { id, name, status, total_pages, created_at, tags, folder } ]

GET    /api/sessions/{id}
       Response: Full session object with tree + timeline + stats

DELETE /api/sessions/{id}
       Deletes session and all associated data

PATCH  /api/sessions/{id}
       Body: { name?, description?, folder_id? }
```

### Processing Status
```
GET    /api/sessions/{id}/status
       Response: { status, progress_percent, current_step, estimated_seconds_remaining }
```

### Steps
```
GET    /api/sessions/{id}/steps
       Response: [ all steps with extracted text + screenshot_url ]

GET    /api/steps/{id}
       Response: Full step object

GET    /api/sessions/{id}/tree
       Response: Full navigation tree JSON
```

### Chat / Q&A
```
POST   /api/sessions/{id}/chat
       Body: { message: string }
       Response: { answer: string, sources: [ { step_id, excerpt, timestamp } ] }

GET    /api/sessions/{id}/chat/history
       Response: [ { role, content, created_at } ]

DELETE /api/sessions/{id}/chat/history
       Clears chat history for session
```

### Search
```
GET    /api/search?q={query}&session_id={optional}
       Response: [ { step_id, session_id, session_name, excerpt, score, timestamp } ]
```

### Annotations
```
GET    /api/steps/{id}/annotations
POST   /api/steps/{id}/annotations    Body: { author_name, content }
DELETE /api/annotations/{id}
```

### Bookmarks
```
GET    /api/sessions/{id}/bookmarks
POST   /api/bookmarks                 Body: { step_id, session_id, label }
DELETE /api/bookmarks/{id}
```

### Tags
```
GET    /api/tags
POST   /api/tags                      Body: { name, color }
POST   /api/sessions/{id}/tags        Body: { tag_id }
DELETE /api/sessions/{id}/tags/{tag_id}
```

### Folders
```
GET    /api/folders
POST   /api/folders                   Body: { name, color }
DELETE /api/folders/{id}
PATCH  /api/folders/{id}              Body: { name?, color? }
```

### Compare
```
POST   /api/compare
       Body: { session_id_a: string, session_id_b: string }
       Response: {
         session_a: { tree, stats },
         session_b: { tree, stats },
         diff: {
           common_pages: [],
           unique_to_a: [],
           unique_to_b: [],
           path_divergence_point: string
         }
       }
```

### Export
```
GET    /api/sessions/{id}/export?format=markdown&include_screenshots=true&include_text=true&include_summaries=true&include_tree=true
       Response: File download
```

### SOP Generation
```
POST   /api/sessions/{id}/sop
       Response: { sop_markdown: string }
```

---

## 8. PROCESSING PIPELINE (Step by Step)

When a video is uploaded, this pipeline runs as a Celery background task:

```
STEP 1 — Frame Extraction
  - Use ffmpeg to extract 1 frame per second
  - Store frames as JPEG in /storage/frames/{session_id}/
  - Update session status = "extracting_frames"

STEP 2 — Page Change Detection
  - Compare consecutive frames using perceptual hashing (imagehash)
  - If hash difference > threshold (40): mark as "significant change"
  - Also use OpenCV structural similarity (SSIM) for confirmation
  - Group consecutive similar frames into "states"
  - Update session status = "detecting_pages"

STEP 3 — OCR on Unique Frames
  - Run EasyOCR only on the first frame of each detected state
  - Extract all text with bounding boxes + confidence scores
  - Preserve reading order (top-to-bottom, left-to-right)
  - Separate large/bold text as likely headings
  - Store raw OCR output per step
  - Update session status = "extracting_text"

STEP 4 — Scroll Deduplication
  - For consecutive frames that are similar but slightly shifted vertically:
    mark as "scroll" event
  - Merge text blocks across scroll frames
  - Remove repeated headers/footers (text that appears in >80% of frames)
  - Keep only unique text content per page
  - Update session status = "deduplicating"

STEP 5 — Navigation Tree Construction
  - Analyze sequence of page states
  - Detect "back" navigation: current page OCR matches a previous page
  - Build parent-child relationships
  - Detect: new page | modal open | tab switch | back navigation
  - Assign depth levels
  - Store tree as JSON
  - Count backtracks
  - Update session status = "building_tree"

STEP 6 — AI Summaries (Claude API)
  - For each page: send extracted text → get 2-3 sentence summary
  - For each step: get 1 sentence description
  - For full session: get executive summary
  - Update session status = "generating_summaries"

STEP 7 — Embeddings + Vector Storage (ChromaDB)
  - For each step: create embedding of extracted_text using sentence-transformers
  - Store in ChromaDB with metadata: { session_id, step_id, page_id, timestamp }
  - Update session status = "indexing"

STEP 8 — Finalize
  - Update session stats (total_pages, total_steps, total_backtracks, total_duration)
  - Save tree JSON to session
  - Update session status = "done"
  - Send processing complete signal to frontend (polling)
```

---

## 9. RAG PIPELINE FOR Q&A

When user asks a question in chat:

```
1. Embed the user question using sentence-transformers
2. Query ChromaDB for top 5 most similar step chunks (filter by session_id)
3. Retrieve full extracted_text for those steps from SQLite
4. Build prompt:
   - System: "You are answering questions about a screen recording session."
   - Context: the 5 retrieved text chunks with their page titles and timestamps
   - User question
5. Call Claude API (claude-sonnet-4-20250514)
6. Return answer + source steps (for citation UI)
7. Save message to chat_messages table
```

---

## 10. ALL UI SCREENS

### Screen 1 — Landing / Upload Page (`/`)
- Hero text: "Turn screen recordings into searchable memory"
- Large drag-and-drop upload zone (accepts MP4, MOV, max 500MB)
- Session name input (required)
- Description input (optional)
- Folder selector dropdown (optional)
- Tag selector (optional)
- [Start Processing] button
- Recent sessions list below (last 5)
- Top nav: Logo | Dashboard | Search | Theme Toggle

### Screen 2 — Processing Status (`/processing/[id]`)
- Session name as heading
- Animated step-by-step progress list:
  - Extracting frames ✓
  - Detecting page changes ✓
  - Running OCR ⟳
  - Building navigation tree ○
  - Generating summaries ○
  - Building search index ○
- Progress bar with percentage
- Estimated time remaining
- Auto-redirects to dashboard when done (poll `/status` every 3 seconds)
- Cancel processing button

### Screen 3 — Main Dashboard (`/dashboard`)
Three-panel layout:

**LEFT PANEL — Session List**
- Folder structure with expand/collapse
- Each session shows: name, date, status badge, tag pills
- [+ New Session] button at top
- Filter by: All | Tag | Folder | Date
- Search sessions by name
- Click session → loads it in center + right panels

**CENTER PANEL — Navigation Tree + Timeline**
- Interactive tree visualization of the session
- Nodes are pages, edges are navigation events
- Backtrack edges shown in different color (orange/amber)
- Click any node → opens Step Detail
- Below tree: horizontal Timeline bar
  - Each step as a colored block
  - Width proportional to time spent
  - Hover shows page name + duration
  - Color coded: blue=forward, orange=backtrack, purple=modal
- Stats bar above tree:
  - Total pages | Total time | Backtracks | Unique content blocks

**RIGHT PANEL — AI Chat**
- Chat interface (messages top, input bottom)
- User messages right-aligned, AI messages left-aligned
- AI answers include source citations (clickable → jumps to step)
- Chat history persists per session
- [Clear History] button
- Suggested questions (3 auto-generated based on session content):
  - "Summarize this session"
  - "What was shown on [first page]?"
  - "Where did the user spend most time?"
- Keyboard shortcut: Ctrl+Enter to send

### Screen 4 — Step Detail View (`/step/[id]`)
- Breadcrumb: Homepage → Pricing → Enterprise
- Left: Screenshot of the frame (full quality)
- Right top: Extracted text (formatted, headings bold)
  - OCR confidence shown as subtle color (low confidence = muted)
  - [Copy Text] button
- Right middle: AI Summary of this step
- Right bottom: Annotations section
  - List of team annotations with author + time
  - [Add Note] text area + submit
- Navigation: ← Previous Step | Next Step →
- Bookmark button (top right of step)
- Back to session button

### Screen 5 — Global Search (`/search`)
- Large search bar at top
- Scope toggle: All Sessions | Current Session
- Results list:
  - Session name → Page name
  - Relevant text excerpt (highlighted matching terms)
  - Timestamp
  - [View Step] button
- Empty state: "Search across everything you've recorded"
- Results update as you type (debounced 400ms)

### Screen 6 — Branch Comparison (`/compare`)
- Two dropdown selectors: Session A | Session B
- [Compare] button
- Side-by-side tree view:
  - Left: Session A tree
  - Right: Session B tree
  - Common pages highlighted in green
  - Unique-to-A pages in blue
  - Unique-to-B pages in purple
  - Divergence point marked with icon
- Stats comparison table below:
  - Total pages | Total time | Backtracks | Unique pages

### Screen 7 — Export (`/export/[id]`)
- Session name as heading
- Format selector:
  - Markdown notes
  - Structured JSON
  - Clean documentation (formatted)
- Checkboxes:
  - Include screenshots
  - Include extracted text
  - Include AI summaries
  - Include navigation tree
  - Include annotations
  - Include SOP
- [Generate SOP] button (calls `/sop` endpoint, shows preview)
- [Export Now] button → downloads file

---

## 11. COMPLETE FEATURE LIST

### Core Features
- [x] Video upload (MP4, MOV, max 500MB)
- [x] Automated frame extraction
- [x] Page change detection
- [x] OCR text extraction with confidence scores
- [x] Scroll deduplication
- [x] Navigation tree with branching
- [x] Backtrack detection and visualization
- [x] Step-by-step timeline
- [x] AI page summaries
- [x] AI session summary
- [x] Q&A chat per session with RAG
- [x] Chat history per session
- [x] Semantic search across all sessions
- [x] Export (Markdown, JSON, Documentation)
- [x] Basic SOP generation

### Organization Features
- [x] Session folders
- [x] Session tags with colors
- [x] Bookmarks on steps
- [x] Team annotations on steps (with author name)

### UI/UX Features
- [x] Dark/Light theme toggle (system default, persists)
- [x] Three-panel dashboard layout
- [x] Interactive navigation tree
- [x] Color-coded timeline heatmap
- [x] Breadcrumb navigation on step view
- [x] Backtrack indicators (different color edges in tree)
- [x] OCR confidence coloring
- [x] Source citations in chat answers
- [x] Suggested questions in chat
- [x] Keyboard shortcuts (Ctrl+Enter for chat, arrow keys for step navigation)
- [x] Processing status page with live updates (polling)
- [x] Session stats bar (pages, time, backtracks)
- [x] Recent sessions on homepage

### Comparison Features
- [x] Side-by-side session comparison (2 sessions)
- [x] Common vs unique page detection
- [x] Path divergence point marking
- [x] Stats comparison table

---

## 12. ENVIRONMENT VARIABLES (`.env`)

```env
# Auth
TEAM_SECRET_TOKEN=your_secret_token_here

# Anthropic
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Storage
STORAGE_PATH=./storage
DATABASE_URL=sqlite:///./database.db
CHROMA_PATH=./chroma_store

# Processing
MAX_VIDEO_SIZE_MB=500
FRAMES_PER_SECOND=1
PAGE_CHANGE_THRESHOLD=40

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_TEAM_TOKEN=your_secret_token_here
```

---

## 13. REQUIREMENTS (Python)

```txt
fastapi
uvicorn
python-multipart
sqlalchemy
celery
redis
opencv-python
imagehash
Pillow
easyocr
ffmpeg-python
sentence-transformers
chromadb
anthropic
python-dotenv
pydantic
aiofiles
```

---

## 14. REQUIREMENTS (Node / Frontend)

```txt
next
react
react-dom
tailwindcss
@shadcn/ui
axios
zustand
lucide-react
@radix-ui/react-*
react-query
d3 (for tree visualization)
```

---

## 15. WHAT NOT TO BUILD (Phase 1 Limits)

Do NOT build:
- Real-time / live processing
- Browser automation or replay
- Autonomous agents
- Advanced visual chart interpretation
- UI component classification
- Multi-user auth with accounts (just shared token)
- Session sharing via link
- Sensitive info blur
- Mobile app

---

## 16. STARTING INSTRUCTIONS FOR CLAUDE CODE

1. Read this entire file first
2. Set up the folder structure exactly as defined in Section 4
3. Start with the backend:
   - Set up FastAPI app with all routers
   - Set up SQLite database with all tables from Section 5
   - Implement the processing pipeline from Section 8
   - Implement all API routes from Section 7
4. Then build the frontend:
   - Set up Next.js 14 with Tailwind + shadcn/ui
   - Build all 7 screens from Section 10
   - Connect to backend via API
5. Make sure dark/light theme works from the start
6. The navigation tree visualization is the most important UI component — use D3.js for it
7. Test the full pipeline with a short MP4 before considering anything done
8. Keep code modular — each service in its own file

**The navigation tree and Q&A chat are the two most important features. Prioritize their quality above everything else.**
