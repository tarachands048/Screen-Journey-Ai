# =============================================================================
# FILE: chat_service.py
# TOPIC: RAG — RETRIEVAL-AUGMENTED GENERATION (the "AG" part)
#
# THEORY RECAP:
#   RAG = Retrieval-Augmented Generation
#   It has two phases:
#     R (Retrieval)  → find relevant chunks from your data (done in embedding_service.py)
#     AG (Augmented Generation) → stuff those chunks into the LLM prompt
#                                  so the LLM answers using YOUR data, not
#                                  just its training data.
#
#   WHY RAG instead of fine-tuning?
#     Fine-tuning: expensive, slow, model forgets other things
#     RAG:         cheap, fast, model keeps all its knowledge AND uses your data
#
# THIS FILE handles the "AG" part:
#   - Takes the retrieved chunks (from embedding_service.py)
#   - Builds a carefully structured prompt with those chunks as context
#   - Sends to Ollama (llama3.2) and gets the answer back
#
# THE FULL RAG FLOW (across files):
#   User types question
#       ↓
#   chat.py (router)          → orchestrates everything
#       ↓
#   embedding_service.py      → converts question → vector, finds top 5 similar steps
#       ↓
#   chat_service.py (THIS)    → builds prompt with those 5 steps as context
#       ↓
#   Ollama / llama3.2         → reads the context + question, generates answer
#       ↓
#   User sees answer + source citations
# =============================================================================

import os
import requests
from typing import List, Dict, Any

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "llama3.2")


# =============================================================================
# MAIN FUNCTION: answer_question()
# This is the heart of the Q&A chat feature.
# =============================================================================

def answer_question(
    session_name: str,
    question: str,
    context_chunks: List[Dict[str, Any]],
    history: List[Dict[str, str]],
) -> str:
    """
    Generates an answer to the user's question using RAG context + chat history.

    PARAMETERS:
      session_name   = name of the session (e.g. "Product Demo Recording")
                       used to orient the LLM about what it's reading
      question       = the user's actual question (e.g. "What was on pricing page?")
      context_chunks = the top 5 most relevant text chunks retrieved from ChromaDB
                       each chunk is a dict:
                         {step_id, excerpt, page_title, timestamp, score}
      history        = the last N chat messages (for multi-turn conversation)
                       each message: {"role": "user"/"assistant", "content": "..."}

    RETURNS:
      A string — the LLM's answer, ready to display in the chat UI.

    ---
    STEP-BY-STEP BREAKDOWN:
    ---

    STEP A: Build the context block
      We format the retrieved chunks into readable text:
        [Source 1 — Pricing Page @ 45s]
        Enterprise plans start at $99/month. Annual billing available...

        [Source 2 — FAQ Page @ 78s]
        Common questions about billing and cancellation...

      WHY FORMAT THIS WAY?
        The LLM needs to know WHERE each piece of information came from
        so it can say "According to the Pricing Page at 45s..."
        This is what enables source citations in the UI.

    STEP B: Build the system message
      This tells the LLM what role to play and what rules to follow.
      KEY RULE: "If the answer is not in the context, say so honestly"
      This prevents hallucination — the LLM making up facts.

    STEP C: Add chat history
      We include the last 6 messages so the LLM has conversation context.
      Example: if the user said "tell me about pricing" and now says
      "what about the enterprise tier?" — the LLM needs the history to
      understand what "it" refers to.
      WHY ONLY 6? Context windows have limits. More history = more tokens = slower.

    STEP D: Add user question
      The question is appended WITH the context chunks embedded in it.
      This is the "augmented" part of RAG — we augment the question with data.

    STEP E: Call Ollama
      Send the full messages list to llama3.2 and return the response.
    """

    # -------------------------------------------------------------------------
    # STEP A: Format retrieved chunks into a context block
    # -------------------------------------------------------------------------
    context_text = ""
    for i, chunk in enumerate(context_chunks, 1):
        page = chunk.get("page_title", "Unknown Page")
        ts = chunk.get("timestamp", 0)          # timestamp in seconds from video start
        excerpt = chunk.get("excerpt", "")       # the actual OCR text from that frame

        # Each source is labelled with its origin (page name + timestamp)
        # The LLM uses these labels when forming its answer ("According to Source 2...")
        context_text += f"\n[Source {i} — {page} @ {ts}s]\n{excerpt}\n"

    # -------------------------------------------------------------------------
    # STEP B: Build the system message (LLM's role + rules)
    # -------------------------------------------------------------------------
    system_msg = (
        "You are an AI assistant answering questions about a screen recording session. "
        "Use the provided context from the recording to answer accurately. "
        "When citing information, mention the page or timestamp. "
        # Critical anti-hallucination rule:
        "If the answer is not in the context, say so honestly."
    )

    # -------------------------------------------------------------------------
    # STEP C: Assemble the messages list
    # This is the "conversation" we send to Ollama.
    # Order matters — system always first, then history, then current question.
    # -------------------------------------------------------------------------
    messages = [{"role": "system", "content": system_msg}]

    # Add recent chat history (last 6 messages = 3 user + 3 assistant turns)
    # This enables multi-turn conversation ("follow-up questions")
    for msg in history[-6:]:
        messages.append({
            "role": msg["role"],        # "user" or "assistant"
            "content": msg["content"],  # the actual text of that message
        })

    # -------------------------------------------------------------------------
    # STEP D: Build the user prompt (question + injected context)
    # -------------------------------------------------------------------------
    # This is the KEY part of RAG — we INJECT the retrieved context
    # directly into the user's message. The LLM reads this and answers
    # based on THIS data, not just what it learned during training.
    user_prompt = (
        f"Session: {session_name}\n\n"
        f"Context from recording:\n{context_text}\n\n"   # ← injected RAG context
        f"Question: {question}"                           # ← the actual user question
    )
    messages.append({"role": "user", "content": user_prompt})

    # -------------------------------------------------------------------------
    # STEP E: Send to Ollama and get the answer
    # -------------------------------------------------------------------------
    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": LLM_MODEL,
                "messages": messages,  # system + history + user question with context
                "stream": False,       # wait for the complete response
            },
            timeout=120,  # LLM generation can take up to 2 minutes
        )
        resp.raise_for_status()

        # Extract just the text from the assistant's response
        # Full response JSON: {"message": {"role": "assistant", "content": "..."}, ...}
        return resp.json()["message"]["content"].strip()

    except Exception as e:
        # If Ollama is not running, return a helpful error message
        return f"Sorry, I couldn't generate an answer right now. ({e})"
