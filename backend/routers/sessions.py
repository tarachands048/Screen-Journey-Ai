import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from models.database import get_db
from models.schemas import Session, SessionListItem, SessionStatusOut
from tasks.processing_pipeline import PROGRESS
from utils.auth import verify_token

router = APIRouter()


@router.get("/sessions", response_model=List[SessionListItem])
def list_sessions(db: DBSession = Depends(get_db), _: str = Depends(verify_token)):
    return db.query(Session).order_by(Session.created_at.desc()).all()


@router.get("/sessions/{session_id}")
def get_session(session_id: str, db: DBSession = Depends(get_db), _: str = Depends(verify_token)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")

    tree_data = None
    if session.tree_json:
        try:
            tree_data = json.loads(session.tree_json)
        except Exception:
            tree_data = None

    return {
        "id": session.id,
        "name": session.name,
        "description": session.description,
        "status": session.status,
        "total_pages": session.total_pages,
        "total_steps": session.total_steps,
        "total_backtracks": session.total_backtracks,
        "total_duration_seconds": session.total_duration_seconds,
        "created_at": session.created_at,
        "processed_at": session.processed_at,
        "session_summary": session.session_summary,
        "tree": tree_data,
        "tags": [{"id": t.id, "name": t.name, "color": t.color} for t in (session.tags or [])],
        "folder": {"id": session.folder.id, "name": session.folder.name} if session.folder else None,
    }


@router.get("/sessions/{session_id}/status", response_model=SessionStatusOut)
def get_status(session_id: str, db: DBSession = Depends(get_db), _: str = Depends(verify_token)):
    progress = PROGRESS.get(session_id)
    if progress:
        return SessionStatusOut(**progress)

    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")

    status_to_percent = {
        "pending": 0, "extracting_frames": 10, "detecting_pages": 25,
        "extracting_text": 40, "deduplicating": 50, "building_tree": 60,
        "generating_summaries": 70, "indexing": 85, "done": 100, "failed": 0,
    }
    pct = status_to_percent.get(session.status, 0)
    return SessionStatusOut(
        status=session.status,
        progress_percent=pct,
        current_step=session.status.replace("_", " ").title(),
        estimated_seconds_remaining=None,
    )


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str, db: DBSession = Depends(get_db), _: str = Depends(verify_token)):
    from services.embedding_service import delete_session_embeddings
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")
    delete_session_embeddings(session_id)
    db.delete(session)
    db.commit()
    return {"deleted": session_id}


@router.patch("/sessions/{session_id}")
def update_session(
    session_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    folder_id: Optional[str] = None,
    db: DBSession = Depends(get_db),
    _: str = Depends(verify_token),
):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")
    if name is not None:
        session.name = name
    if description is not None:
        session.description = description
    if folder_id is not None:
        session.folder_id = folder_id
    db.commit()
    return {"updated": session_id}


@router.get("/sessions/{session_id}/tree")
def get_tree(session_id: str, db: DBSession = Depends(get_db), _: str = Depends(verify_token)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")
    if not session.tree_json:
        return {}
    try:
        return json.loads(session.tree_json)
    except Exception:
        return {}
