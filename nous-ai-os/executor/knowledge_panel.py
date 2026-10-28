"""Document ingestion tracking and local vector relevance search."""
import mimetypes
import os
import sqlite3
from pathlib import Path
from executor.document_intelligence_engine import CHUNKS, load_json
from executor.vector_memory import generate_embedding, cosine_similarity


def _connect():
    path = os.environ.get("NOUS_DB_PATH", "data/nous_storage.db")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE IF NOT EXISTS document_ingestion (id TEXT PRIMARY KEY, status TEXT NOT NULL)")
    return conn


def set_status(document_id, status):
    conn = _connect()
    try:
        with conn:
            conn.execute("INSERT INTO document_ingestion VALUES (?,?) ON CONFLICT(id) DO UPDATE SET status=excluded.status", (document_id, status))
    finally:
        conn.close()


def statuses():
    conn = _connect()
    try:
        return {row["id"]: row["status"] for row in conn.execute("SELECT * FROM document_ingestion")}
    finally:
        conn.close()


def search_documents(query, content_type="", min_score=0.2, limit=20):
    """Reuse NOUS's stable local feature-hash vectors; no external AI calls."""
    query_vector = generate_embedding(query)
    hits = []
    for chunk in load_json(CHUNKS, []):
        if not isinstance(chunk, dict) or not isinstance(chunk.get("text"), str):
            continue
        name = str(chunk.get("document_name", ""))
        mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
        if content_type and not mime.startswith(content_type):
            continue
        score = cosine_similarity(query_vector, generate_embedding(chunk["text"]))
        if score >= min_score:
            hits.append({"id": str(chunk.get("id")), "documentName": name, "text": chunk["text"][:1800], "score": round(score, 4), "contentType": mime})
    return sorted(hits, key=lambda hit: hit["score"], reverse=True)[:limit]