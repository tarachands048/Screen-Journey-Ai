# =============================================================================
# FILE: summary_service.py
# TOPIC: LLM CALLS + PROMPT ENGINEERING
#
# THEORY RECAP:
#   - An LLM (Large Language Model) takes TEXT IN → produces TEXT OUT
#   - You control what it says by carefully crafting the input (the "prompt")
#   - This file is ALL about prompt engineering — how we talk to the AI
#
# IN THIS APP:
#   - After OCR extracts text from frames, we send that text to llama3.2
#     (running locally via Ollama) and ask it to summarize what it saw.
#   - This happens in Step 6 of the processing pipeline.
#   - No internet needed — everything runs on your own machine.
#
# OLLAMA API FORMAT:
#   We send a POST request to http://localhost:11434/api/chat
#   with a list of "messages" — just like OpenAI's ChatGPT API format:
#     [
#       {"role": "system",    "content": "You are a helpful assistant..."},
#       {"role": "user",      "content": "Summarize this page..."},
#       {"role": "assistant", "content": "..."},   ← only in chat history
#     ]
# =============================================================================

import os
import requests
from typing import Optional

# ---------------------------------------------------------------------------
# CONFIG — where is Ollama running, and which model to use
# ---------------------------------------------------------------------------

# Ollama runs a local HTTP server on port 11434
# All LLM requests go through this URL (no internet required)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# llama3.2 is Meta's open-source model (~2GB)
# You can change this to "mistral", "phi3", "gemma2", etc.
LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "llama3.2")


# =============================================================================
# CORE HELPER: _call_ollama()
# All 4 public functions below use this single helper to talk to Ollama.
# This avoids repeating the HTTP request code everywhere.
# =============================================================================

def _call_ollama(prompt: str, system: str = "") -> str:
    """
    Sends a prompt to the local Ollama LLM and returns the response text.

    PARAMETERS:
      prompt  = the actual question or instruction (the "user" message)
      system  = background instructions for the AI (the "system" message)
                This sets the AI's role/persona for this specific call.

    HOW THE MESSAGES LIST WORKS:
      Think of it like a conversation:
        system    → "You are a teacher. Be clear and simple."
        user      → "What is photosynthesis?"
        assistant → "Photosynthesis is..."  ← this is what the LLM generates

      The LLM reads ALL messages in order and generates the next one.
      By choosing the right system message, you control the AI's behavior.

    PROMPT ENGINEERING CONCEPTS USED HERE:
      1. Role prompting: "You are summarizing content from a screen recording"
         → tells the model to stay focused on that specific task
      2. Output format control: "Write a 2-3 sentence summary"
         → constrains what the model produces
      3. Context injection: we paste the actual OCR text into the prompt
         → the model uses that as its source of truth
    """
    # Build the messages list for Ollama's chat API
    messages = []

    # Only add system message if one was provided
    # (not all calls need a system message)
    if system:
        messages.append({"role": "system", "content": system})

    # Always add the user's prompt as the last message
    messages.append({"role": "user", "content": prompt})

    try:
        # POST request to Ollama's chat completion endpoint
        # This is identical in structure to OpenAI's /v1/chat/completions
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": LLM_MODEL,       # which LLM to use
                "messages": messages,      # the conversation so far
                "stream": False,           # False = wait for full response
                                           # True  = stream tokens one by one
            },
            timeout=120,  # LLM can be slow — wait up to 2 minutes
        )

        # Raise exception if server returned an error (4xx / 5xx)
        resp.raise_for_status()

        # The response JSON looks like:
        # {
        #   "model": "llama3.2",
        #   "message": {
        #     "role": "assistant",
        #     "content": "This page shows the pricing options for..."
        #   },
        #   "done": true
        # }
        # We extract just the text content from the assistant's message
        return resp.json()["message"]["content"].strip()

    except Exception as e:
        # If Ollama is down or the model isn't pulled, return a fallback string
        # The app still works — it just won't have AI summaries
        return f"[Summary unavailable: {e}]"


# =============================================================================
# FUNCTION 1: summarize_page()
# Called once per PAGE during video processing (Step 6 of pipeline)
# =============================================================================

def summarize_page(page_title: str, text: str) -> str:
    """
    Generates a 2-3 sentence summary of an entire page using its OCR text.

    CALLED FROM: processing_pipeline.py → Step 6
    STORED IN:   pages.page_summary column in SQLite
    SHOWN IN:    Dashboard (center panel, under page name)

    PROMPT DESIGN CHOICES:
      - We tell it the page title so it has context about what page this is
      - We give it the raw OCR text (capped at 3000 chars to stay within
        the model's context window)
      - We ask for "2-3 sentences" to keep it concise
      - We say "Be concise and factual" to avoid hallucination
    """
    # Guard: don't call the LLM if there's barely any text to summarize
    if not text or len(text.strip()) < 20:
        return "No content extracted for this page."

    # Build the prompt — this is sent as the "user" message
    # Think of it as what you would type to ChatGPT
    prompt = (
        f"Page title: {page_title}\n\n"
        f"Content extracted from screen recording:\n{text[:3000]}\n\n"  # cap at 3000 chars
        "Write a 2-3 sentence summary of what this page shows. Be concise and factual."
    )

    # The system message sets the AI's role for this specific call
    return _call_ollama(
        prompt,
        system="You are summarizing content from a screen recording."
    )


# =============================================================================
# FUNCTION 2: summarize_step()
# Called for the first 20 steps during processing (to keep things fast)
# =============================================================================

def summarize_step(text: str) -> str:
    """
    Generates a single sentence describing what's visible on one video frame.

    CALLED FROM: processing_pipeline.py → Step 6 (first 20 steps only)
    STORED IN:   steps.text_summary column in SQLite
    SHOWN IN:    Session detail page, under each step card

    WHY ONLY 20 STEPS?
      Calling an LLM for every single frame would take too long.
      The first 20 steps cover the most important early frames.
      You could change this limit in processing_pipeline.py.

    PROMPT DESIGN:
      Very short prompt → shorter model output → faster response
      "One sentence" is a hard constraint on output length
    """
    if not text or len(text.strip()) < 10:
        return "Empty or unreadable frame."

    prompt = (
        f"Screen content:\n{text[:1500]}\n\n"        # cap at 1500 chars
        "Describe what is shown on screen in one sentence."
    )

    return _call_ollama(
        prompt,
        system="You are describing screens from a recording."
    )


# =============================================================================
# FUNCTION 3: summarize_session()
# Called ONCE at the end of processing for the whole session
# =============================================================================

def summarize_session(session_name: str, pages_summary: str) -> str:
    """
    Generates a high-level executive summary of the entire recording session.

    CALLED FROM: processing_pipeline.py → Step 6 (after all pages are done)
    STORED IN:   sessions.session_summary column in SQLite
    SHOWN IN:    Dashboard center panel (under session name)

    HOW IT WORKS — "summarize the summaries" pattern:
      1. summarize_page() runs for each page → produces short summaries
      2. Those summaries are joined into pages_summary string
      3. THIS function summarizes THOSE summaries → one overall summary
      This is called "hierarchical summarization" — used in LangChain's
      map-reduce summarization chain.

    PROMPT DESIGN:
      - We give it the session name for context
      - We give it all page summaries joined together (not raw OCR text!)
        This keeps it within the model's context window and focuses on
        what actually matters: the high-level journey.
      - "3-5 sentences" for a meaty but not overwhelming overview
      - We tell it to focus on "journey, key actions, and accomplishments"
        to get useful, structured output
    """
    prompt = (
        f"Session: {session_name}\n\n"
        f"Pages visited:\n{pages_summary[:4000]}\n\n"    # cap at 4000 chars
        "Write a 3-5 sentence executive summary of this screen recording session. "
        "Focus on the user's journey, key actions, and what was accomplished."
    )

    return _call_ollama(
        prompt,
        system="You are summarizing a screen recording session for a team."
    )


# =============================================================================
# FUNCTION 4: generate_suggested_questions()
# Creates 3 starter questions shown in the Chat panel UI
# =============================================================================

def generate_suggested_questions(session_name: str, content_preview: str) -> list[str]:
    """
    Asks the LLM to generate 3 questions a user might want to ask about
    this session. These appear as clickable chips in the chat panel.

    CALLED FROM: (available to call from the frontend/chat panel)
    SHOWN IN:    Chat panel (right panel of Dashboard), before any messages

    PROMPT DESIGN:
      - "Generate exactly 3" → hard number constraint
      - "Return only the questions, one per line, no numbering"
        → controls OUTPUT FORMAT so we can easily parse it with splitlines()
      - We parse the result and fall back to defaults if parsing fails
        (the LLM might not always follow the format exactly)

    FORMAT PARSING:
      The LLM returns something like:
        "What was shown on the pricing page?
         How long did the user spend on checkout?
         What errors appeared during the demo?"
      We split by newlines and filter for lines containing "?"
    """
    prompt = (
        f"Session: {session_name}\n\nContent preview:\n{content_preview[:2000]}\n\n"
        "Generate exactly 3 short questions a user might ask about this screen recording session. "
        "Return only the questions, one per line, no numbering."
    )

    result = _call_ollama(
        prompt,
        system="You are helping users explore screen recording sessions."
    )

    # Parse the LLM's response: split into lines, keep only question lines
    lines = [line.strip() for line in result.splitlines()
             if line.strip() and "?" in line]   # filter lines that look like questions

    # Fallback questions in case parsing fails or LLM doesn't follow format
    default = [
        "Summarize this session",
        "What was shown on the first page?",
        "Where did the user spend the most time?",
    ]

    # Return the first 3 parsed questions, or fallback defaults
    return (lines[:3] if len(lines) >= 3 else default)
