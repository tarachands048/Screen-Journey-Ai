import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv()

from models.database import init_db
from routers import upload, sessions, steps, chat, search, export, annotations, bookmarks, tags, folders, compare

app = FastAPI(title="Screen Journey API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve extracted frames / videos
STORAGE_PATH = os.getenv("STORAGE_PATH", "./storage")
os.makedirs(STORAGE_PATH, exist_ok=True)
app.mount("/storage", StaticFiles(directory=STORAGE_PATH), name="storage")

# Register all routers
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(sessions.router, prefix="/api", tags=["sessions"])
app.include_router(steps.router, prefix="/api", tags=["steps"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(export.router, prefix="/api", tags=["export"])
app.include_router(annotations.router, prefix="/api", tags=["annotations"])
app.include_router(bookmarks.router, prefix="/api", tags=["bookmarks"])
app.include_router(tags.router, prefix="/api", tags=["tags"])
app.include_router(folders.router, prefix="/api", tags=["folders"])
app.include_router(compare.router, prefix="/api", tags=["compare"])


@app.on_event("startup")
def startup():
    init_db()
    os.makedirs(os.path.join(STORAGE_PATH, "videos"), exist_ok=True)
    os.makedirs(os.path.join(STORAGE_PATH, "frames"), exist_ok=True)


@app.get("/")
def root():
    return {"message": "Screen Journey API is running"}


@app.get("/api/health")
def health():
    return {"status": "ok"}
