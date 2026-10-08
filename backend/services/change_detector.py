import os
from typing import List, Tuple

PAGE_CHANGE_THRESHOLD = int(os.getenv("PAGE_CHANGE_THRESHOLD", "40"))


def detect_page_changes(frame_paths: List[str]) -> List[Tuple[int, str]]:
    """
    Compare consecutive frames using perceptual hashing.
    Returns list of (frame_index, frame_path) for frames that represent significant page changes.
    """
    try:
        import imagehash
        from PIL import Image
    except ImportError:
        # If imagehash not available, treat every frame as significant
        return list(enumerate(frame_paths))

    if not frame_paths:
        return []

    significant_frames = [(0, frame_paths[0])]
    prev_hash = None

    for idx, frame_path in enumerate(frame_paths):
        try:
            img = Image.open(frame_path)
            current_hash = imagehash.phash(img)

            if prev_hash is None:
                prev_hash = current_hash
                continue

            diff = abs(current_hash - prev_hash)
            if diff >= PAGE_CHANGE_THRESHOLD:
                significant_frames.append((idx, frame_path))
                prev_hash = current_hash
        except Exception:
            continue

    return significant_frames


def compute_similarity(frame_path_a: str, frame_path_b: str) -> float:
    """Returns structural similarity score 0–1 between two frames."""
    try:
        import cv2
        import numpy as np

        img_a = cv2.imread(frame_path_a, cv2.IMREAD_GRAYSCALE)
        img_b = cv2.imread(frame_path_b, cv2.IMREAD_GRAYSCALE)
        if img_a is None or img_b is None:
            return 0.0

        h = min(img_a.shape[0], img_b.shape[0])
        w = min(img_a.shape[1], img_b.shape[1])
        img_a = cv2.resize(img_a, (w, h))
        img_b = cv2.resize(img_b, (w, h))

        diff = cv2.absdiff(img_a, img_b)
        score = 1.0 - (diff.mean() / 255.0)
        return float(score)
    except Exception:
        return 0.0
