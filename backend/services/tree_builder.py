import json
import re
from typing import List, Dict, Any, Optional

from models.schemas import Step, Page


def _text_similarity(a: str, b: str) -> float:
    """Simple word-overlap similarity between two texts."""
    if not a or not b:
        return 0.0
    words_a = set(re.sub(r"\s+", " ", a.lower()).split())
    words_b = set(re.sub(r"\s+", " ", b.lower()).split())
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / max(len(words_a), len(words_b))


def build_navigation_tree(pages: List[Page], steps: List[Step]) -> Dict[str, Any]:
    """
    Build a recursive navigation tree from pages and their steps.
    Returns a dict matching the SESSION TREE JSON STRUCTURE from the spec.
    """
    if not pages:
        return {}

    # Index pages by id
    page_map = {p.id: p for p in pages}

    # Build tree recursively
    def build_node(page: Page) -> Dict[str, Any]:
        children_pages = [p for p in pages if p.parent_page_id == page.id]
        return {
            "id": page.id,
            "title": page.title or "Unknown Page",
            "depth": page.depth or 0,
            "time_spent": page.time_spent_seconds or 0,
            "timestamp_start": page.first_visited_at or 0,
            "visit_count": page.visit_count or 1,
            "page_summary": page.page_summary,
            "is_backtrack_destination": page.visit_count > 1,
            "children": [build_node(c) for c in sorted(children_pages, key=lambda p: p.sequence_order or 0)],
        }

    # Find root pages (no parent)
    root_pages = [p for p in pages if p.parent_page_id is None]
    root_pages.sort(key=lambda p: p.sequence_order or 0)

    # Build timeline from steps
    timeline = []
    for step in sorted(steps, key=lambda s: s.sequence_order or 0):
        timeline.append({
            "sequence": step.sequence_order,
            "step_id": step.id,
            "page_id": step.page_id,
            "event": step.step_type or "page_load",
            "timestamp": step.timestamp_start or 0,
            "is_backtrack": step.is_backtrack,
        })

    tree_root = build_node(root_pages[0]) if root_pages else {}

    return {
        "tree": tree_root,
        "timeline": timeline,
    }


def detect_backtracks(steps_texts: List[str], similarity_threshold: float = 0.7) -> List[bool]:
    """
    For each step, determine if it is a backtrack (revisit of earlier content).
    Returns a list of booleans parallel to steps_texts.
    """
    is_backtrack = [False] * len(steps_texts)
    for i in range(1, len(steps_texts)):
        for j in range(max(0, i - 10), i):
            if _text_similarity(steps_texts[i], steps_texts[j]) >= similarity_threshold:
                is_backtrack[i] = True
                break
    return is_backtrack


def infer_page_title(text: str) -> str:
    """
    Infer a page title from OCR text.
    Looks for large/prominent text at the top, URL patterns, or heading-like lines.
    """
    if not text:
        return "Unknown Page"

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "Unknown Page"

    # Look for URL pattern
    for line in lines[:5]:
        url_match = re.search(r"https?://\S+|www\.\S+", line)
        if url_match:
            return url_match.group(0)[:80]

    # Return first non-trivial line (likely heading)
    for line in lines[:3]:
        if len(line) > 3 and len(line) < 100:
            return line

    return lines[0][:80] if lines else "Unknown Page"
