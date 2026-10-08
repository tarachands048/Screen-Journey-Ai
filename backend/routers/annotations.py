from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from models.database import get_db
from models.schemas import Annotation, Step, gen_id
from utils.auth import verify_token

router = APIRouter()


class AnnotationCreate(BaseModel):
    author_name: str = ""
    content: str


@router.get("/steps/{step_id}/annotations")
def list_annotations(step_id: str, db: DBSession = Depends(get_db), _: str = Depends(verify_token)):
    annotations = db.query(Annotation).filter(Annotation.step_id == step_id).all()
    return [
        {"id": a.id, "author_name": a.author_name, "content": a.content, "created_at": a.created_at}
        for a in annotations
    ]


@router.post("/steps/{step_id}/annotations")
def add_annotation(
    step_id: str,
    body: AnnotationCreate,
    db: DBSession = Depends(get_db),
    _: str = Depends(verify_token),
):
    step = db.query(Step).filter(Step.id == step_id).first()
    if not step:
        raise HTTPException(404, "Step not found")
    ann = Annotation(
        id=gen_id(),
        step_id=step_id,
        session_id=step.session_id,
        author_name=body.author_name,
        content=body.content,
    )
    db.add(ann)
    db.commit()
    return {"id": ann.id, "author_name": ann.author_name, "content": ann.content, "created_at": ann.created_at}


@router.delete("/annotations/{annotation_id}")
def delete_annotation(annotation_id: str, db: DBSession = Depends(get_db), _: str = Depends(verify_token)):
    ann = db.query(Annotation).filter(Annotation.id == annotation_id).first()
    if not ann:
        raise HTTPException(404, "Annotation not found")
    db.delete(ann)
    db.commit()
    return {"deleted": annotation_id}
