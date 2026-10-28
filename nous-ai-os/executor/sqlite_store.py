"""Durable SQLite-backed memory storage with explicit integrity checks."""
from __future__ import annotations

import json
import os
import sqlite3
import time

DB_PATH = os.environ.get("NOUS_DB_PATH", "data/nous_storage.db")
MAX_MEMORIES = 500


def _get_connection():
    directory = os.path.dirname(DB_PATH) or "."
    os.makedirs(directory, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 15000")
    conn.execute("PRAGMA synchronous = FULL")
    return conn


def init_db():
    conn = _get_connection()
    try:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    data TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_timestamp
                ON memories(timestamp)
            """)
    finally:
        conn.close()


init_db()


def save_memory(entry: dict):
    if not isinstance(entry, dict):
        raise ValueError("memory_entry_must_be_object")
    try:
        encoded = json.dumps(entry, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("memory_entry_not_json_safe") from exc

    conn = _get_connection()
    try:
        with conn:
            conn.execute(
                "INSERT INTO memories (timestamp, data) VALUES (?, ?)",
                (time.time(), encoded),
            )
            conn.execute("""
                DELETE FROM memories WHERE id NOT IN (
                    SELECT id FROM memories ORDER BY id DESC LIMIT ?
                )
            """, (MAX_MEMORIES,))
    finally:
        conn.close()


def load_memories(limit=200) -> list[dict]:
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("memory_limit_must_be_positive_integer")
    limit = min(limit, MAX_MEMORIES)

    conn = _get_connection()
    try:
        rows = conn.execute(
            "SELECT id, data FROM memories ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    finally:
        conn.close()

    # Read newest records efficiently, then return them in chronological order.
    result = []
    for row in reversed(rows):
        try:
            item = json.loads(row["data"])
        except (TypeError, ValueError) as exc:
            raise RuntimeError(f"memory_store_integrity_failure:record:{row['id']}") from exc
        if not isinstance(item, dict):
            raise RuntimeError(f"memory_store_integrity_failure:record_shape:{row['id']}")
        result.append(item)
    return result



def inspect_sqlite_store() -> dict:
    """Return a read-only diagnostic summary of SQLite memory integrity."""
    conn = None
    try:
        conn = _get_connection()
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        row = conn.execute(
            "SELECT COUNT(*) AS count, MAX(timestamp) AS newest FROM memories"
        ).fetchone()
        malformed = 0
        for record in conn.execute("SELECT id, data FROM memories"):
            try:
                decoded = json.loads(record["data"])
                if not isinstance(decoded, dict):
                    malformed += 1
            except (TypeError, ValueError):
                malformed += 1
        return {
            "ok": integrity == "ok" and malformed == 0,
            "database": DB_PATH,
            "integrity_check": integrity,
            "record_count": int(row["count"]),
            "newest_timestamp": row["newest"],
            "malformed_records": malformed,
        }
    except (OSError, sqlite3.Error) as exc:
        return {
            "ok": False,
            "database": DB_PATH,
            "error": "sqlite_store_inspection_failed",
            "details": str(exc),
        }
    finally:
        if conn is not None:
            conn.close()
