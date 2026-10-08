from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session as DBSession

from models.database import get_db
from models.schemas import Folder, gen_id
from utils.auth import verify_token

router = APIRouter()


class FolderCreate(BaseModel):
    name: str
    color: str = "#6366f1"


class FolderUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None


@router.get("/folders")
def list_folders(db: DBSession = Depends(get_db), _: str = Depends(verify_token)):
    return db.query(Folder).order_by(Folder.created_at.desc()).all()


@router.post("/folders")
def create_folder(body: FolderCreate, db: DBSession = Depends(get_db), _: str = Depends(verify_token)):
    folder = Folder(id=gen_id(), name=body.name, color=body.color)
    db.add(folder)
    db.commit()
    return folder


@router.patch("/folders/{folder_id}")
def update_folder(
    folder_id: str,
    body: FolderUpdate,
    db: DBSession = Depends(get_db),
    _: str = Depends(verify_token),
):
    folder = db.query(Folder).filter(Folder.id == folder_id).first()
    if not folder:
        raise HTTPException(404, "Folder not found")
    if body.name is not None:
        folder.name = body.name
    if body.color is not None:
        folder.color = body.color
    db.commit()
    return folder


@router.delete("/folders/{folder_id}")
def delete_folder(folder_id: str, db: DBSession = Depends(get_db), _: str = Depends(verify_token)):
    folder = db.query(Folder).filter(Folder.id == folder_id).first()
    if not folder:
        raise HTTPException(404, "Folder not found")
    db.delete(folder)
    db.commit()
    return {"deleted": folder_id}
