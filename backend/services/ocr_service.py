import os
import re
from typing import Tuple

TESSERACT_CMD = os.getenv("TESSERACT_CMD", "tesseract")


def _setup_tesseract():
    try:
        import pytesseract
        if TESSERACT_CMD and TESSERACT_CMD != "tesseract":
            pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
        return pytesseract
    except ImportError:
        return None


def extract_text(image_path: str) -> Tuple[str, float]:
    """
    Extract text from an image using pytesseract.
    Returns (text, confidence_score).
    """
    pytesseract = _setup_tesseract()
    if pytesseract is None:
        return "", 0.0

    try:
        from PIL import Image
        img = Image.open(image_path)

        # Get text with confidence data
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        texts = []
        confidences = []

        for i, text in enumerate(data["text"]):
            text = text.strip()
            conf = int(data["conf"][i])
            if text and conf > 0:
                texts.append(text)
                confidences.append(conf)

        full_text = " ".join(texts)
        avg_confidence = (sum(confidences) / len(confidences) / 100.0) if confidences else 0.0

        return full_text, avg_confidence
    except Exception:
        return "", 0.0


def redact_sensitive(text: str) -> str:
    """Remove obvious sensitive patterns (emails, credit cards, passwords)."""
    text = re.sub(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", "[EMAIL]", text)
    text = re.sub(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b", "[CARD]", text)
    text = re.sub(r"(?i)(password|passwd|pwd)\s*[:=]\s*\S+", r"\1: [REDACTED]", text)
    return text
