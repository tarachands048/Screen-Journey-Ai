"""
Full video processing pipeline — runs in a background thread via FastAPI BackgroundTasks.
Progress is tracked in the global PROGRESS dict keyed by session_id.
"""
import json
import time
import traceback
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session as DBSession

from models.database import SessionLocal
from models.schemas import Session, Page, Step, NavEvent, gen_id
from services.video_processor import extract_frames
from services.change_detector import detect_page_changes
from services.ocr_service import extract_text
from services.scroll_deduplicator import merge_page_texts
from services.tree_builder import detect_backtracks, infer_page_title, build_navigation_tree
from services.summary_service import summarize_page, summarize_step, summarize_session
from services.embedding_service import index_step

# Global progress tracker: { session_id: { status, progress_percent, current_step } }
PROGRESS: dict[str, dict] = {}


def _update_progress(session_id: str, status: str, percent: int, step_label: str):
    PROGRESS[session_id] = {
        "status": status,
        "progress_percent": percent,
        "current_step": step_label,
        "estimated_seconds_remaining": None,
    }


def run_pipeline(session_id: str, video_path: str):
    db: DBSession = SessionLocal()
    try:
        _update_progress(session_id, "processing", 0, "Starting pipeline")

        session = db.query(Session).filter(Session.id == session_id).first()
        if not session:
            return

        # STEP 1 — Frame extraction
        _update_progress(session_id, "processing", 5, "Extracting frames")
        session.status = "extracting_frames"
        db.commit()

        frame_paths, duration = extract_frames(video_path, session_id)
        if not frame_paths:
            session.status = "failed"
            db.commit()
            return

        session.total_duration_seconds = duration
        db.commit()

        # STEP 2 — Page change detection
        _update_progress(session_id, "processing", 20, "Detecting page changes")
        session.status = "detecting_pages"
        db.commit()

        significant_frames = detect_page_changes(frame_paths)

        # STEP 3 — OCR on unique frames
        _update_progress(session_id, "processing", 35, "Extracting text (OCR)")
        session.status = "extracting_text"
        db.commit()

        ocr_results = []
        for frame_idx, frame_path in significant_frames:
            text, confidence = extract_text(frame_path)
            ocr_results.append({
                "frame_idx": frame_idx,
                "frame_path": frame_path,
                "text": text,
                "confidence": confidence,
                "timestamp": frame_idx,
            })

        # STEP 4 — Scroll deduplication (merge nearby frames with similar content)
        _update_progress(session_id, "processing", 45, "Deduplicating content")
        session.status = "deduplicating"
        db.commit()

        # Group consecutive frames into page-groups by similarity
        pages_raw = _group_into_pages(ocr_results)

        # STEP 5 — Navigation tree construction
        _update_progress(session_id, "processing", 55, "Building navigation tree")
        session.status = "building_tree"
        db.commit()

        all_texts = [pg["merged_text"] for pg in pages_raw]
        is_backtrack_list = detect_backtracks(all_texts)

        # Determine parent-child structure
        page_records = []
        step_records = []
        nav_events = []

        page_stack = []
        prev_step_id = None

        for i, page_data in enumerate(pages_raw):
            is_back = is_backtrack_list[i]
            page_title = infer_page_title(page_data["merged_text"])
            merged_text = page_data["merged_text"]

            # Determine parent
            parent_id = page_stack[-1] if page_stack and not is_back else None
            depth = len(page_stack)

            # For backtracks, find the matching earlier page
            if is_back and page_stack:
                depth = max(0, len(page_stack) - 1)
                parent_id = page_stack[-2] if len(page_stack) >= 2 else None
                page_stack.pop()

            page_id = gen_id()
            page_rec = Page(
                id=page_id,
                session_id=session_id,
                title=page_title,
                parent_page_id=parent_id,
                depth=depth,
                first_visited_at=page_data["timestamp_start"],
                last_visited_at=page_data["timestamp_end"],
                time_spent_seconds=page_data["timestamp_end"] - page_data["timestamp_start"],
                sequence_order=i,
            )
            page_records.append(page_rec)
            db.add(page_rec)

            if not is_back:
                page_stack.append(page_id)

            # Create step records for this page
            for j, frame_data in enumerate(page_data["frames"]):
                step_id = gen_id()
                step_rec = Step(
                    id=step_id,
                    session_id=session_id,
                    page_id=page_id,
                    step_type="back_navigation" if is_back else ("page_load" if j == 0 else "scroll"),
                    screenshot_path=frame_data["frame_path"],
                    extracted_text=frame_data["text"],
                    timestamp_start=frame_data["timestamp"],
                    timestamp_end=frame_data["timestamp"] + 1,
                    ocr_confidence=frame_data["confidence"],
                    sequence_order=len(step_records),
                    is_backtrack=is_back and j == 0,
                )
                step_records.append(step_rec)
                db.add(step_rec)

                if prev_step_id:
                    event = NavEvent(
                        id=gen_id(),
                        session_id=session_id,
                        from_step_id=prev_step_id,
                        to_step_id=step_id,
                        event_type="back" if is_back else "forward",
                        timestamp=frame_data["timestamp"],
                    )
                    nav_events.append(event)
                    db.add(event)

                prev_step_id = step_id

        db.commit()

        # STEP 6 — AI summaries via Ollama
        _update_progress(session_id, "processing", 65, "Generating AI summaries")
        session.status = "generating_summaries"
        db.commit()

        pages_summary_parts = []
        for page_rec in page_records:
            merged = next((pg["merged_text"] for pg in pages_raw
                          if pg["timestamp_start"] == page_rec.first_visited_at), "")
            summary = summarize_page(page_rec.title or "Page", merged)
            page_rec.page_summary = summary
            pages_summary_parts.append(f"{page_rec.title}: {summary}")

        # Summarize steps (first few)
        for step_rec in step_records[:20]:
            if step_rec.extracted_text:
                step_rec.text_summary = summarize_step(step_rec.extracted_text)

        session_summary = summarize_session(
            session.name,
            "\n".join(pages_summary_parts),
        )
        session.session_summary = session_summary
        db.commit()

        # STEP 7 — Embeddings + ChromaDB indexing
        _update_progress(session_id, "processing", 80, "Building search index")
        session.status = "indexing"
        db.commit()

        for step_rec in step_records:
            if step_rec.extracted_text:
                index_step(
                    session_id=session_id,
                    step_id=step_rec.id,
                    page_id=step_rec.page_id or "",
                    text=step_rec.extracted_text,
                    timestamp=step_rec.timestamp_start or 0,
                )

        # STEP 8 — Finalize
        _update_progress(session_id, "processing", 95, "Finalizing")

        tree_data = build_navigation_tree(page_records, step_records)
        session.tree_json = json.dumps(tree_data)
        session.total_pages = len(page_records)
        session.total_steps = len(step_records)
        session.total_backtracks = sum(1 for s in step_records if s.is_backtrack)
        session.status = "done"
        session.processed_at = datetime.utcnow()
        db.commit()

        _update_progress(session_id, "done", 100, "Complete")

    except Exception:
        traceback.print_exc()
        try:
            session = db.query(Session).filter(Session.id == session_id).first()
            if session:
                session.status = "failed"
                db.commit()
        except Exception:
            pass
        _update_progress(session_id, "failed", 0, "Pipeline failed")
    finally:
        db.close()


def _group_into_pages(ocr_results: list, similarity_threshold: float = 0.6) -> list:
    """
    Group consecutive OCR frames into page-level groups.
    Returns list of page dicts with merged text.
    """
    if not ocr_results:
        return []

    def text_similarity(a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        words_a = set(a.lower().split())
        words_b = set(b.lower().split())
        if not words_a or not words_b:
            return 0.0
        return len(words_a & words_b) / max(len(words_a), len(words_b))

    groups = []
    current_group = [ocr_results[0]]

    for result in ocr_results[1:]:
        prev_text = current_group[-1]["text"]
        curr_text = result["text"]
        sim = text_similarity(prev_text, curr_text)
        if sim >= similarity_threshold:
            current_group.append(result)
        else:
            groups.append(current_group)
            current_group = [result]

    if current_group:
        groups.append(current_group)

    page_groups = []
    for group in groups:
        merged_text = merge_page_texts([r["text"] for r in group])
        page_groups.append({
            "frames": group,
            "merged_text": merged_text,
            "timestamp_start": group[0]["timestamp"],
            "timestamp_end": group[-1]["timestamp"],
        })

    return page_groups
