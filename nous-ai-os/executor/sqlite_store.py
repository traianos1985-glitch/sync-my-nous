"""Durable SQLite storage for NOUS memory records."""
from __future__ import annotations

import json
import os
import sqlite3
import time
from typing import Any

DB_PATH = "data/nous_storage.db"
MAX_RECORDS = 500
DEFAULT_LOAD_LIMIT = 200


def _get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 15000")
    return conn


def init_db() -> None:
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


def save_memory(entry: dict[str, Any]) -> dict[str, Any]:
    """Save one JSON-serializable memory and enforce the retention limit."""
    if not isinstance(entry, dict):
        raise TypeError("memory_entry_must_be_object")
    try:
        encoded = json.dumps(entry, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("memory_entry_not_json_serializable") from exc

    conn = _get_connection()
    try:
        with conn:
            cursor = conn.execute(
                "INSERT INTO memories (timestamp, data) VALUES (?, ?)",
                (time.time(), encoded),
            )
            record_id = cursor.lastrowid
            conn.execute("""
                DELETE FROM memories
                WHERE id NOT IN (
                    SELECT id FROM memories ORDER BY id DESC LIMIT ?
                )
            """, (MAX_RECORDS,))
        return {"ok": True, "id": record_id}
    finally:
        conn.close()


def load_memories(limit: int = DEFAULT_LOAD_LIMIT) -> list[dict[str, Any]]:
    """Return the newest records in chronological order; never hide corrupt rows."""
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_RECORDS:
        raise ValueError(f"limit_must_be_integer_between_1_and_{MAX_RECORDS}")

    conn = _get_connection()
    try:
        rows = conn.execute("""
            SELECT id, data FROM (
                SELECT id, data FROM memories ORDER BY id DESC LIMIT ?
            )
            ORDER BY id ASC
        """, (limit,)).fetchall()
    finally:
        conn.close()

    result: list[dict[str, Any]] = []
    for row in rows:
        try:
            item = json.loads(row["data"])
        except (TypeError, ValueError) as exc:
            raise RuntimeError(f"sqlite_memory_integrity_failure:invalid_json:id={row['id']}") from exc
        if not isinstance(item, dict):
            raise RuntimeError(f"sqlite_memory_integrity_failure:invalid_record_shape:id={row['id']}")
        result.append(item)
    return result


def inspect_sqlite_store() -> dict[str, Any]:
    """Read-only health report suitable for diagnostics and support bundles."""
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
        ok = integrity == "ok" and malformed == 0
        return {
            "ok": ok,
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
