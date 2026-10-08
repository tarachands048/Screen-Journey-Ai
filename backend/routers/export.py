import json
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session as DBSession

from models.database import get_db
from models.schemas import Session, Page, Step
from services.export_service import export_markdown, export_json
from services.sop_generator import generate_sop
from utils.auth import verify_token

router = APIRouter()


@router.get("/sessions/{session_id}/export")
def export_session(
    session_id: str,
    format: str = Query("markdown", pattern="^(markdown|json|documentation)$"),
    include_screenshots: bool = Query(False),
    include_text: bool = Query(True),
    include_summaries: bool = Query(True),
    include_tree: bool = Query(True),
    include_annotations: bool = Query(True),
    include_sop: bool = Query(False),
    db: DBSession = Depends(get_db),
    _: str = Depends(verify_token),
):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")

    pages = db.query(Page).filter(Page.session_id == session_id).order_by(Page.sequence_order).all()
    steps = db.query(Step).filter(Step.session_id == session_id).order_by(Step.sequence_order).all()

    sop_content = None
    if include_sop:
        steps_data = [
            {
                "page_title": next((p.title for p in pages if p.id == s.page_id), "Unknown"),
                "step_type": s.step_type,
                "text_summary": s.text_summary,
                "extracted_text": s.extracted_text,
                "timestamp_start": s.timestamp_start,
            }
            for s in steps
        ]
        sop_content = generate_sop(session.name, steps_data)

    if format in ("markdown", "documentation"):
        content = export_markdown(
            session, pages, steps,
            include_screenshots=include_screenshots,
            include_text=include_text,
            include_summaries=include_summaries,
            include_tree=include_tree,
            include_annotations=include_annotations,
            sop_content=sop_content,
        )
        filename = f"{session.name.replace(' ', '_')}_export.md"
        return Response(
            content=content,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    else:
        tree_data = json.loads(session.tree_json) if session.tree_json else None
        content = export_json(session, pages, steps, tree_data=tree_data)
        filename = f"{session.name.replace(' ', '_')}_export.json"
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )


@router.post("/sessions/{session_id}/sop")
def generate_session_sop(
    session_id: str,
    db: DBSession = Depends(get_db),
    _: str = Depends(verify_token),
):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")

    pages = db.query(Page).filter(Page.session_id == session_id).all()
    steps = db.query(Step).filter(Step.session_id == session_id).order_by(Step.sequence_order).all()

    steps_data = [
        {
            "page_title": next((p.title for p in pages if p.id == s.page_id), "Unknown"),
            "step_type": s.step_type,
            "text_summary": s.text_summary,
            "extracted_text": s.extracted_text,
            "timestamp_start": s.timestamp_start,
        }
        for s in steps
    ]
    sop = generate_sop(session.name, steps_data)
    return {"sop_markdown": sop}
