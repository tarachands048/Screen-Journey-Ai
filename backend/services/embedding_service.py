# =============================================================================
# FILE: embedding_service.py
# TOPIC: EMBEDDINGS + VECTOR DATABASE (ChromaDB)
#
# THEORY RECAP (connecting what you learned to this code):
#   - An "embedding" is just a list of numbers (e.g. 768 numbers) that
#     represents the MEANING of a piece of text.
#   - Two texts that mean similar things will have similar numbers → they
#     are "close" to each other in vector space.
#   - A Vector Database stores those lists of numbers and lets you search
#     by meaning instead of by keyword.
#
# IN THIS APP:
#   1. When a video is processed → each frame's OCR text is turned into
#      an embedding and stored in ChromaDB.
#   2. When a user types a question in chat → the question is also turned
#      into an embedding and we find the stored texts with closest meaning.
#   3. Those closest texts become the "context" that gets sent to the AI.
#      (This is the R in RAG — Retrieval-Augmented Generation)
# =============================================================================

import os
import requests
from typing import List, Optional

# ---------------------------------------------------------------------------
# CONFIGURATION — read from .env file
# ---------------------------------------------------------------------------

# Ollama is the local AI server running on your machine (port 11434 by default)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# nomic-embed-text is the embedding model — it converts text → vectors
# It's a small model (274 MB) that runs fast on CPU
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

# ChromaDB will store its data in this folder on disk
# (so embeddings survive even if you restart the server)
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_store")

# ---------------------------------------------------------------------------
# LAZY SINGLETON PATTERN
# We don't connect to ChromaDB when the module loads — only when first needed.
# This avoids slowing down server startup.
# ---------------------------------------------------------------------------
_chroma_client = None   # the ChromaDB connection object
_collection = None      # the specific "table" inside ChromaDB we use


def _get_collection():
    """
    Returns the ChromaDB collection (like a table in a regular database).
    Creates it on first call, then reuses the same connection every time.

    CHROMADB CONCEPT:
      - ChromaDB organises data into "collections" (similar to tables in SQL
        or indexes in Elasticsearch).
      - Each item in a collection has:
          id        → unique identifier (we use the step_id from SQLite)
          embedding → the list of numbers (the vector)
          document  → the original text (stored so we can show it in results)
          metadata  → extra info like session_id, timestamp (for filtering)
    """
    global _chroma_client, _collection

    # If already initialised, just return the existing collection
    if _collection is not None:
        return _collection

    try:
        import chromadb

        # PersistentClient = save data to disk (survives restarts)
        # vs. EphemeralClient = in-memory only (lost on restart)
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

        # get_or_create_collection:
        #   - If the collection "screen_steps" already exists → open it
        #   - If it doesn't exist yet → create it fresh
        #
        # metadata={"hnsw:space": "cosine"}
        #   This tells ChromaDB HOW to measure distance between vectors.
        #   "cosine" = cosine similarity (angle between vectors, not length)
        #   This is better for text because it ignores how long the text is
        #   and focuses purely on meaning/direction.
        _collection = _chroma_client.get_or_create_collection(
            name="screen_steps",
            metadata={"hnsw:space": "cosine"},
        )
    except Exception:
        # If ChromaDB isn't installed or fails, set to None
        # The rest of the code checks for None and skips gracefully
        _collection = None

    return _collection


# =============================================================================
# FUNCTION 1: _embed()  ← THE CORE OF EVERYTHING
# =============================================================================

def _embed(text: str) -> Optional[List[float]]:
    """
    Converts a piece of text into an embedding (a list of floating-point numbers).

    WHAT IS AN EMBEDDING?
      Input:  "The user clicked on the pricing page"
      Output: [0.023, -0.412, 0.891, 0.003, -0.227, ...]  ← 768 numbers

    WHY 768 NUMBERS?
      nomic-embed-text is trained to represent meaning in 768 dimensions.
      Each dimension captures some aspect of meaning (though you can't
      directly interpret individual dimensions — they're learned patterns).

    HOW IT WORKS (theory → code):
      - We send the text to Ollama's /api/embeddings endpoint over HTTP
      - Ollama runs the nomic-embed-text model locally on your machine
      - The model returns a JSON response with the embedding array
      - We return that array to be stored in ChromaDB

    Returns None if:
      - The text is empty
      - Ollama is not running
      - Any network/model error occurs
    """
    # Don't try to embed empty text — it wastes time and produces bad vectors
    if not text or not text.strip():
        return None

    try:
        # Send HTTP POST request to Ollama's local embedding API
        # This is identical to what LangChain's OllamaEmbeddings does internally
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",   # Ollama embedding endpoint
            json={
                "model": EMBED_MODEL,              # which model to use
                "prompt": text[:4000],             # cap at 4000 chars (model limit)
            },
            timeout=60,  # wait max 60 seconds before giving up
        )

        # Raise an error if Ollama returned a non-200 HTTP status
        resp.raise_for_status()

        # The response looks like: {"embedding": [0.023, -0.412, 0.891, ...]}
        # We extract just the array of numbers
        return resp.json()["embedding"]

    except Exception:
        # Ollama might not be running, or model not pulled yet
        # Return None so the caller can handle the failure gracefully
        return None


# =============================================================================
# FUNCTION 2: index_step()  ← STORING EMBEDDINGS (called during processing)
# =============================================================================

def index_step(session_id: str, step_id: str, page_id: str, text: str, timestamp: int):
    """
    Converts OCR text from one video frame into an embedding and stores it
    in ChromaDB. Called by the processing pipeline for every step.

    WHEN IS THIS CALLED?
      In processing_pipeline.py → Step 7 (Embeddings + Vector Storage):
        for step in all_steps:
            index_step(session_id, step.id, step.page_id, step.extracted_text, ...)

    WHAT GETS STORED (think of it like a row in a database table):
      id        = step_id         (the unique key — same as SQLite step ID)
      embedding = [0.023, ...]    (768 numbers representing the text's meaning)
      document  = "Enterprise...  (the original text, truncated to 2000 chars)
      metadata  = {               (extra fields we can filter by later)
          "session_id": "abc-123",
          "step_id":    "xyz-789",
          "page_id":    "pqr-456",
          "timestamp":  45,        ← seconds from start of video
      }
    """
    # Step 1: Get the ChromaDB collection (or None if unavailable)
    collection = _get_collection()

    # Skip if ChromaDB failed to initialise, or if there's no text to store
    if collection is None or not text:
        return

    # Step 2: Convert the OCR text → embedding vector
    embedding = _embed(text)

    # Skip if embedding failed (Ollama not running, etc.)
    if embedding is None:
        return

    try:
        # Step 3: Store in ChromaDB using upsert
        # "upsert" = update if ID exists, insert if ID doesn't exist
        # This means re-processing a session won't create duplicate entries
        collection.upsert(
            ids=[step_id],             # unique ID (list because ChromaDB is batch-capable)
            embeddings=[embedding],    # the vector [0.023, -0.412, ...] (list of lists)
            documents=[text[:2000]],   # original text (capped at 2000 chars for storage)
            metadatas=[{               # extra info for filtering
                "session_id": session_id,
                "step_id": step_id,
                "page_id": page_id or "",
                "timestamp": timestamp or 0,
            }],
        )
    except Exception:
        # If storing fails, just skip — the step data is still safe in SQLite
        pass


# =============================================================================
# FUNCTION 3: search_steps()  ← SEMANTIC SEARCH (called during chat)
# =============================================================================

def search_steps(query: str, session_id: Optional[str] = None, top_k: int = 5) -> List[dict]:
    """
    Finds the most semantically similar steps to the user's question.
    This is the "R" (Retrieval) in RAG — Retrieval-Augmented Generation.

    HOW IT WORKS:
      1. Convert user's query → embedding (same process as storing)
      2. ChromaDB compares this query vector against ALL stored vectors
         using cosine similarity (angle between vectors in 768-D space)
      3. Returns the top_k results whose vectors are closest to the query

    KEYWORD SEARCH vs SEMANTIC SEARCH:
      Keyword: "pricing page" → only finds steps with exact words "pricing page"
      Semantic: "pricing page" → also finds "cost", "subscription plans",
                "monthly billing" because they MEAN similar things

    PARAMETERS:
      query      = the user's question e.g. "What was on the pricing page?"
      session_id = if provided, only search within this session's steps
      top_k      = how many results to return (we use 5 for the RAG context)

    RETURNS:
      List of dicts, each with:
        step_id   → so we can look up the full step in SQLite
        session_id, page_id, timestamp → metadata
        excerpt   → the original text (first 300 chars)
        score     → similarity score (0.0 to 1.0, higher = more similar)
    """
    collection = _get_collection()
    if collection is None:
        return []

    # Step 1: Embed the user's question
    # IMPORTANT: We use the SAME model (nomic-embed-text) to embed the query
    # as we used when storing. If you used different models, the vectors
    # would be in different "spaces" and comparison would be meaningless.
    embedding = _embed(query)
    if embedding is None:
        return []

    # Step 2: Build an optional filter
    # If session_id is given, only search steps belonging to that session.
    # This is metadata filtering — ChromaDB filters BEFORE doing vector search,
    # which makes it faster and ensures results are from the right session.
    where = {"session_id": session_id} if session_id else None

    try:
        # Step 3: Query ChromaDB
        # This is the actual vector similarity search.
        # ChromaDB uses HNSW (Hierarchical Navigable Small World) algorithm
        # to efficiently find nearest neighbors in 768-dimensional space
        # without comparing against every single stored vector.
        results = collection.query(
            query_embeddings=[embedding],              # our query vector (list of lists)
            n_results=top_k,                           # return top 5 closest matches
            where=where,                               # metadata filter
            include=["documents", "metadatas", "distances"],  # what to return
        )

        # Step 4: Format the results
        # results["documents"][0]  → list of original texts for the top matches
        # results["metadatas"][0]  → list of metadata dicts
        # results["distances"][0]  → list of cosine distances (0=identical, 2=opposite)
        output = []
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i]
            dist = results["distances"][0][i]   # cosine distance (lower = more similar)

            # Convert distance → similarity score
            # Cosine distance ranges from 0 (identical) to 2 (opposite)
            # Score = 1 - distance gives us: 1.0 (identical) to -1.0 (opposite)
            # In practice, scores above 0.7 are very relevant matches
            output.append({
                "step_id":    meta.get("step_id"),
                "session_id": meta.get("session_id"),
                "page_id":    meta.get("page_id"),
                "timestamp":  meta.get("timestamp"),
                "excerpt":    doc[:300],                # first 300 chars of original text
                "score":      round(1 - dist, 3),       # similarity score (3 decimal places)
            })

        return output

    except Exception:
        return []


# =============================================================================
# FUNCTION 4: delete_session_embeddings()  ← CLEANUP
# =============================================================================

def delete_session_embeddings(session_id: str):
    """
    Removes all stored embeddings for a session from ChromaDB.
    Called when a session is deleted from the app, to keep ChromaDB clean.

    WHY WE NEED THIS:
      ChromaDB and SQLite are two separate databases.
      When we delete a session from SQLite, ChromaDB doesn't know about it.
      So we manually delete the matching embeddings here.
    """
    collection = _get_collection()
    if collection is None:
        return
    try:
        # Delete all items where metadata field session_id matches
        collection.delete(where={"session_id": session_id})
    except Exception:
        pass
