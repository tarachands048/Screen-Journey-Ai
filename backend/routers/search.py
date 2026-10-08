from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session as DBSession

from models.database import get_db
from models.schemas import Step, Session, Page
from services.embedding_service import search_steps
from utils.auth import verify_token

router = APIRouter()


@router.get("/search")
def search(
    q: str = Query(..., min_length=1),
    session_id: Optional[str] = Query(None),
    db: DBSession = Depends(get_db),
    _: str = Depends(verify_token),
):
    raw = search_steps(q, session_id=session_id, top_k=20)

    results = []
    for r in raw:
        step = db.query(Step).filter(Step.id == r["step_id"]).first()
        if not step:
            continue
        session = db.query(Session).filter(Session.id == step.session_id).first()
        page_title = None
        if step.page_id:
            page = db.query(Page).filter(Page.id == step.page_id).first()
            if page:
                page_title = page.title

        results.append({
            "step_id": r["step_id"],
            "session_id": step.session_id,
            "session_name": session.name if session else "Unknown",
            "page_title": page_title,
            "excerpt": r["excerpt"],
            "score": r["score"],
            "timestamp": r.get("timestamp"),
        })

    return results
