from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from models.database import get_db
from models.schemas import Bookmark, Step, gen_id
from utils.auth import verify_token

router = APIRouter()


class BookmarkCreate(BaseModel):
    step_id: str
    session_id: str
    label: str = ""


@router.get("/sessions/{session_id}/bookmarks")
def list_bookmarks(session_id: str, db: DBSession = Depends(get_db), _: str = Depends(verify_token)):
    bookmarks = db.query(Bookmark).filter(Bookmark.session_id == session_id).all()
    return [
        {"id": b.id, "step_id": b.step_id, "label": b.label, "created_at": b.created_at}
        for b in bookmarks
    ]


@router.post("/bookmarks")
def create_bookmark(body: BookmarkCreate, db: DBSession = Depends(get_db), _: str = Depends(verify_token)):
    step = db.query(Step).filter(Step.id == body.step_id).first()
    if not step:
        raise HTTPException(404, "Step not found")
    bm = Bookmark(
        id=gen_id(),
        step_id=body.step_id,
        session_id=body.session_id,
        label=body.label,
    )
    db.add(bm)
    db.commit()
    return {"id": bm.id, "step_id": bm.step_id, "label": bm.label, "created_at": bm.created_at}


@router.delete("/bookmarks/{bookmark_id}")
def delete_bookmark(bookmark_id: str, db: DBSession = Depends(get_db), _: str = Depends(verify_token)):
    bm = db.query(Bookmark).filter(Bookmark.id == bookmark_id).first()
    if not bm:
        raise HTTPException(404, "Bookmark not found")
    db.delete(bm)
    db.commit()
    return {"deleted": bookmark_id}
