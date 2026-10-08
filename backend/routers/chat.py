# =============================================================================
# FILE: routers/chat.py
# TOPIC: RAG ORCHESTRATION — the "glue" that connects all the pieces
#
# WHAT THIS FILE DOES:
#   This is the API route handler for the chat feature.
#   It receives the user's message from the frontend (React) and
#   ORCHESTRATES the full RAG pipeline:
#
#   1. Validate the request (is this session real? is the token valid?)
#   2. RETRIEVE: call embedding_service → find top 5 similar steps
#   3. ENRICH: look up page titles for each retrieved step (from SQLite)
#   4. LOAD HISTORY: get previous messages (for multi-turn conversation)
#   5. GENERATE: call chat_service → build prompt → call LLM → get answer
#   6. SAVE: store both user message and AI answer in SQLite
#   7. RESPOND: send answer + source citations back to the frontend
#
# WHERE IT SITS IN THE ARCHITECTURE:
#   Browser (React) → HTTP POST /api/sessions/{id}/chat
#                           ↓
#                     THIS FILE (router)
#                      ↓          ↓
#              embedding_service  chat_service
#                 (ChromaDB)       (Ollama LLM)
#                      ↓          ↓
#                    SQLite (save chat history)
#                           ↓
#                     HTTP Response → Browser shows answer
# =============================================================================

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from models.database import get_db
from models.schemas import Session, ChatMessage, Step, Page, gen_id
from services.embedding_service import search_steps    # ← the R in RAG
from services.chat_service import answer_question      # ← the AG in RAG
from utils.auth import verify_token

router = APIRouter()


# =============================================================================
# REQUEST SCHEMA
# Pydantic validates the incoming JSON body automatically.
# If the frontend sends { "message": "What was on the pricing page?" }
# Pydantic maps it to this class. If "message" is missing → 422 error.
# =============================================================================

class ChatRequest(BaseModel):
    message: str   # the user's question, e.g. "What was shown on the first page?"


# =============================================================================
# ROUTE 1: POST /api/sessions/{session_id}/chat
# THE MAIN CHAT ENDPOINT — Full RAG pipeline runs here
# =============================================================================

@router.post("/sessions/{session_id}/chat")
def chat(
    session_id: str,             # from URL: which session are we chatting about?
    body: ChatRequest,           # from request body: {"message": "..."}
    db: DBSession = Depends(get_db),         # SQLite connection (injected by FastAPI)
    _: str = Depends(verify_token),          # auth check (must send X-Team-Token header)
):
    """
    Handles a single chat message and returns an AI-generated answer.

    DEPENDS():
      FastAPI's dependency injection system automatically:
        - Opens a database connection and passes it as `db`
        - Calls verify_token() and raises 401 if token is wrong
      You don't call these manually — FastAPI handles it before your code runs.
    """

    # ------------------------------------------------------------------
    # GUARD: Make sure the session actually exists in the database
    # ------------------------------------------------------------------
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")

    # ==================================================================
    # STEP 1: RETRIEVAL (the "R" in RAG)
    # Convert the user's question to a vector and find the 5 most
    # semantically similar steps in ChromaDB.
    #
    # search_steps() does:
    #   a) Calls Ollama /api/embeddings to get a vector for the question
    #   b) Queries ChromaDB with that vector
    #   c) Returns top 5 matches with step_id, excerpt, score, timestamp
    #
    # session_id filter = only search THIS session's steps, not all sessions
    # top_k=5 = return top 5 most relevant results
    # ==================================================================
    raw_results = search_steps(body.message, session_id=session_id, top_k=5)

    # ==================================================================
    # STEP 2: ENRICH RESULTS WITH PAGE TITLES
    # ChromaDB only stores metadata (session_id, step_id, timestamp).
    # The page title is stored in SQLite, so we do a quick lookup for each
    # result to add the human-readable page name.
    # This is what allows the LLM to say "According to the Pricing Page..."
    # ==================================================================
    context_chunks = []
    for r in raw_results:
        # Look up the step in SQLite to get its page_id
        step = db.query(Step).filter(Step.id == r["step_id"]).first()

        page_title = "Unknown Page"
        if step and step.page_id:
            # Look up the page in SQLite to get its human-readable title
            page = db.query(Page).filter(Page.id == step.page_id).first()
            if page:
                page_title = page.title or "Unknown Page"

        # Merge the ChromaDB result with the SQLite page title
        context_chunks.append({
            **r,                      # spread all ChromaDB fields (step_id, excerpt, score...)
            "page_title": page_title, # add the page title from SQLite
        })

    # ==================================================================
    # STEP 3: LOAD CHAT HISTORY (for multi-turn conversation)
    # We retrieve the last 20 messages from SQLite.
    # These are passed to chat_service.py where we use the last 6
    # (3 back-and-forth turns) to give the LLM conversation context.
    #
    # WHY STORE IN SQLITE?
    #   If we only kept history in memory, it would be lost on server restart.
    #   SQLite persists history between sessions.
    # ==================================================================
    history_records = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())  # oldest first → correct time order
        .limit(20)                               # last 20 messages max
        .all()
    )
    # Convert SQLAlchemy objects → simple dicts that chat_service.py expects
    history = [{"role": m.role, "content": m.content} for m in history_records]

    # ==================================================================
    # STEP 4: GENERATE ANSWER (the "AG" in RAG)
    # Pass everything to chat_service.py which:
    #   a) Formats context_chunks into a readable context block
    #   b) Builds the full messages list (system + history + user prompt)
    #   c) Sends to Ollama and returns the response text
    # ==================================================================
    answer = answer_question(
        session_name=session.name,        # e.g. "Product Demo Recording"
        question=body.message,            # e.g. "What was on the pricing page?"
        context_chunks=context_chunks,    # the 5 relevant chunks from ChromaDB + page titles
        history=history,                  # recent conversation for multi-turn support
    )

    # ==================================================================
    # STEP 5: SAVE BOTH MESSAGES TO SQLITE
    # We store user message AND AI response so chat history persists.
    # gen_id() creates a new UUID for each message.
    # db.commit() writes both to disk atomically.
    # ==================================================================
    db.add(ChatMessage(
        id=gen_id(),
        session_id=session_id,
        role="user",          # "user" = came from the human
        content=body.message, # original question
    ))
    db.add(ChatMessage(
        id=gen_id(),
        session_id=session_id,
        role="assistant",     # "assistant" = came from the AI
        content=answer,       # generated answer
    ))
    db.commit()  # write both rows to SQLite in one transaction

    # ==================================================================
    # STEP 6: RETURN RESPONSE TO FRONTEND
    # The React ChatPanel component reads:
    #   answer  → displays as the AI message bubble
    #   sources → displays as small citation chips below the message
    #             ("Source: Pricing Page @ 45s")
    # ==================================================================
    return {
        "answer": answer,
        "sources": [
            {
                "step_id":    c["step_id"],            # so UI can link to that step
                "excerpt":    c["excerpt"],            # short preview of the source text
                "timestamp":  c.get("timestamp"),      # seconds in video (for reference)
                "page_title": c.get("page_title"),     # human-readable page name
                "score":      c.get("score"),          # similarity score (0.0 → 1.0)
            }
            for c in context_chunks
        ],
    }


# =============================================================================
# ROUTE 2: GET /api/sessions/{session_id}/chat/history
# Returns all previous messages for a session (to restore chat on page load)
# =============================================================================

@router.get("/sessions/{session_id}/chat/history")
def get_chat_history(
    session_id: str,
    db: DBSession = Depends(get_db),
    _: str = Depends(verify_token),
):
    """
    Loads the full chat history for a session.

    CALLED BY: ChatPanel.tsx when the user switches to a session.
    The frontend stores no local state — it always loads from the backend.
    This means chat history survives browser refreshes and new devices.
    """
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())  # chronological order for display
        .all()
    )

    # Return as a simple list of dicts (no SQLAlchemy objects in HTTP responses)
    return [
        {
            "id":         m.id,
            "role":       m.role,       # "user" or "assistant"
            "content":    m.content,
            "created_at": m.created_at,
        }
        for m in messages
    ]


# =============================================================================
# ROUTE 3: DELETE /api/sessions/{session_id}/chat/history
# Wipes all chat messages for this session (the "Clear History" button)
# =============================================================================

@router.delete("/sessions/{session_id}/chat/history")
def clear_chat_history(
    session_id: str,
    db: DBSession = Depends(get_db),
    _: str = Depends(verify_token),
):
    """
    Deletes all chat messages for a session from SQLite.
    Does NOT affect the vector embeddings in ChromaDB — only the conversation log.
    """
    # .delete() on a query deletes all matching rows in one SQL DELETE statement
    # More efficient than loading records and deleting one by one
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.commit()
    return {"cleared": session_id}
