from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from models.database import get_db
from models.schemas import Tag, Session, gen_id, session_tags
from utils.auth import verify_token

router = APIRouter()


class TagCreate(BaseModel):
    name: str
    color: str = "#6366f1"


class TagAssign(BaseModel):
    tag_id: str


@router.get("/tags")
def list_tags(db: DBSession = Depends(get_db), _: str = Depends(verify_token)):
    return db.query(Tag).all()


@router.post("/tags")
def create_tag(body: TagCreate, db: DBSession = Depends(get_db), _: str = Depends(verify_token)):
    existing = db.query(Tag).filter(Tag.name == body.name).first()
    if existing:
        return existing
    tag = Tag(id=gen_id(), name=body.name, color=body.color)
    db.add(tag)
    db.commit()
    return tag


@router.post("/sessions/{session_id}/tags")
def assign_tag(
    session_id: str,
    body: TagAssign,
    db: DBSession = Depends(get_db),
    _: str = Depends(verify_token),
):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")
    tag = db.query(Tag).filter(Tag.id == body.tag_id).first()
    if not tag:
        raise HTTPException(404, "Tag not found")
    if tag not in session.tags:
        session.tags.append(tag)
        db.commit()
    return {"session_id": session_id, "tag_id": body.tag_id}


@router.delete("/sessions/{session_id}/tags/{tag_id}")
def remove_tag(
    session_id: str,
    tag_id: str,
    db: DBSession = Depends(get_db),
    _: str = Depends(verify_token),
):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if tag and tag in session.tags:
        session.tags.remove(tag)
        db.commit()
    return {"removed": tag_id}
