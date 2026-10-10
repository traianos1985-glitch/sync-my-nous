"""Durable SQLite-backed memory storage with explicit integrity checks."""
from __future__ import annotations

import json
import os
import sqlite3
import time

DB_PATH = "data/nous_storage.db"
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
