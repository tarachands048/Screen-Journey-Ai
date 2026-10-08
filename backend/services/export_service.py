import json
from datetime import datetime
from typing import List, Any, Dict, Optional

from models.schemas import Session, Step, Page


def export_markdown(
    session: Session,
    pages: List[Page],
    steps: List[Step],
    include_screenshots: bool = False,
    include_text: bool = True,
    include_summaries: bool = True,
    include_tree: bool = True,
    include_annotations: bool = True,
    sop_content: Optional[str] = None,
) -> str:
    lines = []
    lines.append(f"# {session.name}")
    lines.append(f"\n> Exported on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    if session.description:
        lines.append(f"\n{session.description}")

    lines.append(f"\n## Session Overview")
    lines.append(f"- **Total Pages:** {session.total_pages}")
    lines.append(f"- **Total Steps:** {session.total_steps}")
    lines.append(f"- **Duration:** {session.total_duration_seconds or 0}s")
    lines.append(f"- **Backtracks:** {session.total_backtracks}")

    if session.session_summary and include_summaries:
        lines.append(f"\n### Summary\n{session.session_summary}")

    if include_tree and session.tree_json:
        lines.append(f"\n## Navigation Tree\n```json\n{session.tree_json}\n```")

    if pages:
        lines.append("\n## Pages")
        for page in sorted(pages, key=lambda p: p.sequence_order or 0):
            indent = "  " * (page.depth or 0)
            lines.append(f"\n{indent}### {'→ ' * (page.depth or 0)}{page.title or 'Unknown'}")
            lines.append(f"{indent}*Time spent: {page.time_spent_seconds or 0}s | First visited: {page.first_visited_at or 0}s*")
            if page.page_summary and include_summaries:
                lines.append(f"\n{indent}{page.page_summary}")

    if steps:
        lines.append("\n## Steps")
        step_map: Dict[str, List[Step]] = {}
        for step in steps:
            page_id = step.page_id or "unknown"
            step_map.setdefault(page_id, []).append(step)

        for page in sorted(pages, key=lambda p: p.sequence_order or 0):
            page_steps = sorted(step_map.get(page.id, []), key=lambda s: s.sequence_order or 0)
            if not page_steps:
                continue
            lines.append(f"\n### {page.title or 'Unknown Page'}")
            for step in page_steps:
                lines.append(f"\n**[{step.timestamp_start or 0}s]** `{step.step_type or 'action'}`")
                if step.text_summary and include_summaries:
                    lines.append(f"_{step.text_summary}_")
                if step.extracted_text and include_text:
                    lines.append(f"\n```\n{step.extracted_text[:500]}\n```")
                if include_screenshots and step.screenshot_path:
                    lines.append(f"\n![Screenshot]({step.screenshot_path})")

    if sop_content:
        lines.append(f"\n---\n\n{sop_content}")

    return "\n".join(lines)


def export_json(
    session: Session,
    pages: List[Page],
    steps: List[Step],
    tree_data: Optional[Dict] = None,
) -> str:
    data = {
        "session": {
            "id": session.id,
            "name": session.name,
            "description": session.description,
            "status": session.status,
            "total_pages": session.total_pages,
            "total_steps": session.total_steps,
            "total_duration_seconds": session.total_duration_seconds,
            "total_backtracks": session.total_backtracks,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "session_summary": session.session_summary,
        },
        "pages": [
            {
                "id": p.id,
                "title": p.title,
                "depth": p.depth,
                "parent_page_id": p.parent_page_id,
                "time_spent_seconds": p.time_spent_seconds,
                "first_visited_at": p.first_visited_at,
                "page_summary": p.page_summary,
            }
            for p in sorted(pages, key=lambda p: p.sequence_order or 0)
        ],
        "steps": [
            {
                "id": s.id,
                "page_id": s.page_id,
                "step_type": s.step_type,
                "timestamp_start": s.timestamp_start,
                "timestamp_end": s.timestamp_end,
                "extracted_text": s.extracted_text,
                "text_summary": s.text_summary,
                "is_backtrack": s.is_backtrack,
                "ocr_confidence": s.ocr_confidence,
            }
            for s in sorted(steps, key=lambda s: s.sequence_order or 0)
        ],
        "tree": tree_data,
    }
    return json.dumps(data, indent=2, default=str)
