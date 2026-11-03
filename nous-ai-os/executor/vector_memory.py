"""Long-term Vector Memory & Semantic Search for NOUS.

Provides lightweight, zero-dependency embedding generation and cosine similarity search
persisted in SQLite for long-term memory retrieval and RAG.
"""
import sqlite3
import json
import math
import os
import re
import time
import zlib

from executor import shared_state_store
from typing import Any, Dict, List, Optional, Tuple

DB_PATH = "data/nous_storage.db"
EMBEDDING_DIM = 128

def _get_connection():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_vector_db():
    conn = _get_connection()
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vector_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                metadata TEXT,
                embedding TEXT NOT NULL,
                timestamp REAL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_vec_timestamp ON vector_memories(timestamp)
        """)
    conn.close()

init_vector_db()

def _tokenize(text: str) -> List[str]:
    return [w.lower() for w in re.findall(r"\w+", text, flags=re.UNICODE) if len(w) > 1]

def _stable_hash(value: str) -> int:
    # Built-in hash() is salted per process, so stored embeddings would not match later queries.
    return zlib.crc32(value.encode("utf-8"))

def generate_embedding(text: str, dim: int = EMBEDDING_DIM) -> List[float]:
    """Generates a normalized semantic vector using feature hashing with n-grams."""
    tokens = _tokenize(text)
    if not tokens:
        return [0.0] * dim

    vec = [0.0] * dim
    # Unigrams and bigrams for context
    ngrams = list(tokens)
    for i in range(len(tokens) - 1):
        ngrams.append(f"{tokens[i]}_{tokens[i+1]}")

    for gram in ngrams:
        # Multi-hash to reduce collision bias
        h1 = _stable_hash(gram) % dim
        h2 = _stable_hash(gram[::-1]) % dim
        weight = 1.0 if "_" not in gram else 1.5
        vec[h1] += weight
        vec[h2] += weight * 0.5

    # Normalize to unit vector
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if len(v1) != len(v2) or not v1:
        return 0.0
    return sum(a * b for a, b in zip(v1, v2))

def store_vector_memory(text: str, metadata: Optional[Dict[str, Any]] = None) -> int | str:
    """Stores a memory snippet and embedding; Neon mode shares the bounded index."""
    if not text.strip():
        return -1
    emb = generate_embedding(text)
    if shared_state_store.cloud_enabled():
        import uuid
        record = {"id": str(uuid.uuid4()), "text": text.strip(), "metadata": metadata or {}, "embedding": emb, "timestamp": time.time()}
        with shared_state_store.edit_state("data/vector_memories.json", []) as rows:
            if not isinstance(rows, list):
                raise RuntimeError("vector_memory_integrity_failure")
            # Import the device's SQLite vectors on the first cloud write.
            if not rows and os.path.exists(DB_PATH):
                legacy = _get_connection()
                try:
                    old_rows = legacy.execute(
                        "SELECT id, text, metadata, embedding, timestamp FROM vector_memories ORDER BY id DESC LIMIT 1000"
                    ).fetchall()
                    for old in reversed(old_rows):
                        try:
                            rows.append({
                                "id": f"legacy:{old['id']}",
                                "text": old["text"],
                                "metadata": json.loads(old["metadata"]) if old["metadata"] else {},
                                "embedding": json.loads(old["embedding"]),
                                "timestamp": old["timestamp"],
                            })
                        except (TypeError, ValueError, json.JSONDecodeError):
                            continue
                finally:
                    legacy.close()
            rows.append(record)
            del rows[:-1000]
        return record["id"]
    conn = _get_connection()
    with conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO vector_memories (text, metadata, embedding, timestamp) VALUES (?, ?, ?, ?)",
            (text.strip(), json.dumps(metadata or {}, ensure_ascii=False), json.dumps(emb), time.time())
        )
        row_id = cur.lastrowid
        # Keep maximum 1000 vector records
        conn.execute("""
            DELETE FROM vector_memories WHERE id NOT IN (
                SELECT id FROM vector_memories ORDER BY id DESC LIMIT 1000
            )
        """)
    conn.close()
    return row_id

def search_vector_memory(query: str, top_k: int = 5, min_score: float = 0.05) -> List[Dict[str, Any]]:
    """Performs semantic cosine similarity search across vector memories."""
    q_emb = generate_embedding(query)
    if shared_state_store.cloud_enabled():
        rows = shared_state_store.read_state("data/vector_memories.json", [])
        results = []
        for row in rows if isinstance(rows, list) else []:
            try:
                score = cosine_similarity(q_emb, row["embedding"])
                if score >= min_score:
                    results.append({**row, "similarity": round(score, 4)})
            except (KeyError, TypeError, ValueError):
                continue
        results.sort(key=lambda item: item["similarity"], reverse=True)
        return results[:max(1, min(int(top_k), 100))]
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, text, metadata, embedding, timestamp FROM vector_memories ORDER BY id DESC LIMIT 500")
    rows = cur.fetchall()
    conn.close()

    results: List[Tuple[float, Dict[str, Any]]] = []
    for row in rows:
        try:
            emb = json.loads(row["embedding"])
            score = cosine_similarity(q_emb, emb)
            if score >= min_score:
                meta = json.loads(row["metadata"]) if row["metadata"] else {}
                results.append((score, {
                    "id": row["id"],
                    "text": row["text"],
                    "metadata": meta,
                    "similarity": round(score, 4),
                    "timestamp": row["timestamp"]
                }))
        except Exception:
            continue

    results.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in results[:top_k]]

def get_vector_stats() -> Dict[str, Any]:
    if shared_state_store.cloud_enabled():
        rows = shared_state_store.read_state("data/vector_memories.json", [])
        return {"total_vectors": len(rows) if isinstance(rows, list) else 0, "dimensions": EMBEDDING_DIM, "status": "healthy"}
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as total FROM vector_memories")
    total = cur.fetchone()["total"]
    conn.close()
    return {
        "total_vectors": total,
        "dimensions": EMBEDDING_DIM,
        "status": "healthy"
    }
