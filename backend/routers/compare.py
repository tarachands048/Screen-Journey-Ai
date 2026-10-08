import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from models.database import get_db
from models.schemas import Session, Page
from utils.auth import verify_token

router = APIRouter()


class CompareRequest(BaseModel):
    session_id_a: str
    session_id_b: str


@router.post("/compare")
def compare_sessions(
    body: CompareRequest,
    db: DBSession = Depends(get_db),
    _: str = Depends(verify_token),
):
    session_a = db.query(Session).filter(Session.id == body.session_id_a).first()
    session_b = db.query(Session).filter(Session.id == body.session_id_b).first()

    if not session_a or not session_b:
        raise HTTPException(404, "One or both sessions not found")

    pages_a = db.query(Page).filter(Page.session_id == body.session_id_a).all()
    pages_b = db.query(Page).filter(Page.session_id == body.session_id_b).all()

    titles_a = {(p.title or "").lower().strip() for p in pages_a}
    titles_b = {(p.title or "").lower().strip() for p in pages_b}

    common = titles_a & titles_b
    unique_a = titles_a - titles_b
    unique_b = titles_b - titles_a

    # Find first divergence point
    pages_a_sorted = sorted(pages_a, key=lambda p: p.sequence_order or 0)
    pages_b_sorted = sorted(pages_b, key=lambda p: p.sequence_order or 0)
    divergence_point = None
    for pa, pb in zip(pages_a_sorted, pages_b_sorted):
        if (pa.title or "").lower() != (pb.title or "").lower():
            divergence_point = pa.title
            break

    def session_stats(session: Session, pages: list) -> dict:
        return {
            "id": session.id,
            "name": session.name,
            "total_pages": session.total_pages,
            "total_steps": session.total_steps,
            "total_duration_seconds": session.total_duration_seconds,
            "total_backtracks": session.total_backtracks,
            "tree": json.loads(session.tree_json) if session.tree_json else None,
            "pages": [{"id": p.id, "title": p.title, "depth": p.depth} for p in pages],
        }

    return {
        "session_a": session_stats(session_a, pages_a),
        "session_b": session_stats(session_b, pages_b),
        "diff": {
            "common_pages": list(common),
            "unique_to_a": list(unique_a),
            "unique_to_b": list(unique_b),
            "path_divergence_point": divergence_point,
        },
    }
