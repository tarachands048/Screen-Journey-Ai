import os
import requests
from typing import List, Dict, Any

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "llama3.2")


def generate_sop(session_name: str, steps_data: List[Dict[str, Any]]) -> str:
    """
    Generate a Standard Operating Procedure document from session steps.
    steps_data: list of {page_title, step_type, text_summary, timestamp_start}
    """
    steps_text = ""
    for i, step in enumerate(steps_data[:50], 1):
        page = step.get("page_title", "Unknown Page")
        summary = step.get("text_summary") or step.get("extracted_text", "")[:200]
        step_type = step.get("step_type", "action")
        ts = step.get("timestamp_start", 0)
        steps_text += f"Step {i} [{ts}s] ({step_type}) on '{page}': {summary}\n"

    prompt = (
        f"Session recording: {session_name}\n\n"
        f"Navigation steps:\n{steps_text}\n\n"
        "Convert these screen recording steps into a clear Standard Operating Procedure (SOP) document. "
        "Format it as:\n"
        "# SOP: [task name]\n\n"
        "## Purpose\n[1-2 sentences]\n\n"
        "## Prerequisites\n[bullet list]\n\n"
        "## Steps\n[numbered list with clear instructions]\n\n"
        "## Notes\n[any important observations]\n\n"
        "Write it as if instructing someone to perform this task for the first time. Use Markdown."
    )

    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": LLM_MODEL,
                "messages": [
                    {"role": "system", "content": "You are writing Standard Operating Procedures from screen recordings."},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
            },
            timeout=180,
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"].strip()
    except Exception as e:
        return f"# SOP Generation Failed\n\nError: {e}"
