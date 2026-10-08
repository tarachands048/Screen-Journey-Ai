from typing import List
import re


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def _overlap_ratio(a: str, b: str) -> float:
    """Rough word-level overlap between two texts."""
    words_a = set(_normalize(a).split())
    words_b = set(_normalize(b).split())
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / min(len(words_a), len(words_b))


def deduplicate_steps(texts: List[str], threshold: float = 0.85) -> List[str]:
    """
    Given OCR text for a sequence of frames on the same page,
    merge them into a single deduplicated text block.
    Removes repeated headers/footers (lines appearing in >80% of frames).
    """
    if not texts:
        return texts

    # Split each text into lines
    lines_per_frame = [set(t.splitlines()) for t in texts]

    # Find lines that appear in >80% of frames (repeated nav/header/footer)
    total = len(texts)
    global_counts: dict[str, int] = {}
    for line_set in lines_per_frame:
        for line in line_set:
            norm = _normalize(line)
            if norm:
                global_counts[norm] = global_counts.get(norm, 0) + 1

    repeated = {norm for norm, cnt in global_counts.items() if cnt / total > 0.8}

    # Build merged unique content
    seen_norms: set[str] = set()
    merged_lines: List[str] = []

    for text in texts:
        for line in text.splitlines():
            norm = _normalize(line)
            if not norm:
                continue
            if norm in repeated:
                continue
            if norm not in seen_norms:
                seen_norms.add(norm)
                merged_lines.append(line.strip())

    return merged_lines


def merge_page_texts(texts: List[str]) -> str:
    merged = deduplicate_steps(texts)
    return "\n".join(merged)
