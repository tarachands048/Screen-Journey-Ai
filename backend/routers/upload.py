import os
import threading
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from models.database import get_db
from models.schemas import Session, gen_id
from utils.auth import verify_token
from utils.file_utils import get_video_path
from tasks.processing_pipeline import run_pipeline

router = APIRouter()

MAX_SIZE_MB = int(os.getenv("MAX_VIDEO_SIZE_MB", "500"))


@router.post("/upload")
async def upload_video(
    video: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(""),
    folder_id: str = Form(None),
    db: DBSession = Depends(get_db),
    _: str = Depends(verify_token),
):
    if not video.filename.lower().endswith((".mp4", ".mov", ".avi", ".mkv")):
        raise HTTPException(400, "Unsupported video format. Use MP4 or MOV.")

    content = await video.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_SIZE_MB:
        raise HTTPException(400, f"File too large. Max {MAX_SIZE_MB}MB.")

    session_id = gen_id()
    video_path = get_video_path(session_id, video.filename)

    with open(video_path, "wb") as f:
        f.write(content)

    session = Session(
        id=session_id,
        name=name,
        description=description or None,
        video_path=video_path,
        status="pending",
        folder_id=folder_id or None,
    )
    db.add(session)
    db.commit()

    # Start pipeline in background thread
    t = threading.Thread(target=run_pipeline, args=(session_id, video_path), daemon=True)
    t.start()

    return {"session_id": session_id, "status": "processing"}
