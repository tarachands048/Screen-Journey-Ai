from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from models.database import get_db
from models.schemas import Step, StepOut
from utils.auth import verify_token

router = APIRouter()


@router.get("/sessions/{session_id}/steps")
def list_steps(session_id: str, db: DBSession = Depends(get_db), _: str = Depends(verify_token)):
    steps = (
        db.query(Step)
        .filter(Step.session_id == session_id)
        .order_by(Step.sequence_order)
        .all()
    )
    return [_step_out(s) for s in steps]


@router.get("/steps/{step_id}")
def get_step(step_id: str, db: DBSession = Depends(get_db), _: str = Depends(verify_token)):
    step = db.query(Step).filter(Step.id == step_id).first()
    if not step:
        raise HTTPException(404, "Step not found")
    return _step_out(step)


def _step_out(step: Step) -> dict:
    screenshot_url = None
    if step.screenshot_path:
        import os
        rel = step.screenshot_path.replace("\\", "/")
        screenshot_url = f"/storage/{rel.lstrip('./storage/')}"

    return {
        "id": step.id,
        "session_id": step.session_id,
        "page_id": step.page_id,
        "step_type": step.step_type,
        "screenshot_path": step.screenshot_path,
        "screenshot_url": screenshot_url,
        "extracted_text": step.extracted_text,
        "text_summary": step.text_summary,
        "timestamp_start": step.timestamp_start,
        "timestamp_end": step.timestamp_end,
        "ocr_confidence": step.ocr_confidence,
        "sequence_order": step.sequence_order,
        "is_backtrack": step.is_backtrack,
    }
