import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime,
    ForeignKey, Table
)
from sqlalchemy.orm import relationship
from pydantic import BaseModel

from models.database import Base


def gen_id():
    return str(uuid.uuid4())


# ── SQLAlchemy ORM models ──────────────────────────────────────────────────────

class Folder(Base):
    __tablename__ = "folders"
    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    color = Column(String, default="#6366f1")
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("Session", back_populates="folder")


class Session(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    description = Column(Text)
    video_path = Column(String)
    status = Column(String, default="pending")
    total_duration_seconds = Column(Integer)
    total_pages = Column(Integer, default=0)
    total_steps = Column(Integer, default=0)
    total_backtracks = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    folder_id = Column(String, ForeignKey("folders.id"), nullable=True)
    session_summary = Column(Text)
    tree_json = Column(Text)

    folder = relationship("Folder", back_populates="sessions")
    pages = relationship("Page", back_populates="session", cascade="all, delete-orphan")
    steps = relationship("Step", back_populates="session", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="session_tags", back_populates="sessions")
    chat_messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    annotations = relationship("Annotation", back_populates="session", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="session", cascade="all, delete-orphan")


class Page(Base):
    __tablename__ = "pages"
    id = Column(String, primary_key=True, default=gen_id)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    title = Column(String)
    url_or_identifier = Column(String)
    parent_page_id = Column(String, ForeignKey("pages.id"), nullable=True)
    depth = Column(Integer, default=0)
    visit_count = Column(Integer, default=1)
    first_visited_at = Column(Integer)
    last_visited_at = Column(Integer)
    time_spent_seconds = Column(Integer)
    page_summary = Column(Text)
    sequence_order = Column(Integer)

    session = relationship("Session", back_populates="pages")
    steps = relationship("Step", back_populates="page")

    # Self-referential relationship: a page can have child pages (navigation tree)
    # remote_side=[id] tells SQLAlchemy: "id is on the ONE side (parent)"
    # so parent_page_id is on the MANY side (children)
    children = relationship(
        "Page",
        back_populates="parent",
        foreign_keys="[Page.parent_page_id]",
    )
    parent = relationship(
        "Page",
        back_populates="children",
        foreign_keys="[Page.parent_page_id]",
        remote_side="[Page.id]",
    )


class Step(Base):
    __tablename__ = "steps"
    id = Column(String, primary_key=True, default=gen_id)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    page_id = Column(String, ForeignKey("pages.id"), nullable=True)
    step_type = Column(String)
    screenshot_path = Column(String)
    extracted_text = Column(Text)
    text_summary = Column(Text)
    timestamp_start = Column(Integer)
    timestamp_end = Column(Integer)
    ocr_confidence = Column(Float)
    sequence_order = Column(Integer)
    is_backtrack = Column(Boolean, default=False)

    session = relationship("Session", back_populates="steps")
    page = relationship("Page", back_populates="steps")
    annotations = relationship("Annotation", back_populates="step", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="step", cascade="all, delete-orphan")


class NavEvent(Base):
    __tablename__ = "nav_events"
    id = Column(String, primary_key=True, default=gen_id)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    from_step_id = Column(String, ForeignKey("steps.id"), nullable=True)
    to_step_id = Column(String, ForeignKey("steps.id"), nullable=True)
    event_type = Column(String)
    timestamp = Column(Integer)


class Annotation(Base):
    __tablename__ = "annotations"
    id = Column(String, primary_key=True, default=gen_id)
    step_id = Column(String, ForeignKey("steps.id"), nullable=False)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    author_name = Column(String)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    step = relationship("Step", back_populates="annotations")
    session = relationship("Session", back_populates="annotations")


class Bookmark(Base):
    __tablename__ = "bookmarks"
    id = Column(String, primary_key=True, default=gen_id)
    step_id = Column(String, ForeignKey("steps.id"), nullable=False)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    label = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    step = relationship("Step", back_populates="bookmarks")
    session = relationship("Session", back_populates="bookmarks")


class Tag(Base):
    __tablename__ = "tags"
    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, unique=True, nullable=False)
    color = Column(String, default="#6366f1")

    sessions = relationship("Session", secondary="session_tags", back_populates="tags")


session_tags = Table(
    "session_tags",
    Base.metadata,
    Column("session_id", String, ForeignKey("sessions.id"), primary_key=True),
    Column("tag_id", String, ForeignKey("tags.id"), primary_key=True),
)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(String, primary_key=True, default=gen_id)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    role = Column(String)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="chat_messages")


# ── Pydantic response schemas ──────────────────────────────────────────────────

class TagOut(BaseModel):
    id: str
    name: str
    color: str
    model_config = {"from_attributes": True}


class FolderOut(BaseModel):
    id: str
    name: str
    color: str
    created_at: datetime
    model_config = {"from_attributes": True}


class SessionListItem(BaseModel):
    id: str
    name: str
    description: Optional[str]
    status: str
    total_pages: int
    total_steps: int
    total_backtracks: int
    created_at: datetime
    processed_at: Optional[datetime]
    tags: List[TagOut] = []
    folder: Optional[FolderOut] = None
    model_config = {"from_attributes": True}


class StepOut(BaseModel):
    id: str
    session_id: str
    page_id: Optional[str]
    step_type: Optional[str]
    screenshot_path: Optional[str]
    extracted_text: Optional[str]
    text_summary: Optional[str]
    timestamp_start: Optional[int]
    timestamp_end: Optional[int]
    ocr_confidence: Optional[float]
    sequence_order: Optional[int]
    is_backtrack: bool
    model_config = {"from_attributes": True}


class PageOut(BaseModel):
    id: str
    session_id: str
    title: Optional[str]
    url_or_identifier: Optional[str]
    parent_page_id: Optional[str]
    depth: int
    visit_count: int
    first_visited_at: Optional[int]
    last_visited_at: Optional[int]
    time_spent_seconds: Optional[int]
    page_summary: Optional[str]
    sequence_order: Optional[int]
    model_config = {"from_attributes": True}


class AnnotationOut(BaseModel):
    id: str
    step_id: str
    session_id: str
    author_name: Optional[str]
    content: str
    created_at: datetime
    model_config = {"from_attributes": True}


class BookmarkOut(BaseModel):
    id: str
    step_id: str
    session_id: str
    label: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}


class ChatMessageOut(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    created_at: datetime
    model_config = {"from_attributes": True}


class SessionStatusOut(BaseModel):
    status: str
    progress_percent: int
    current_step: str
    estimated_seconds_remaining: Optional[int]
