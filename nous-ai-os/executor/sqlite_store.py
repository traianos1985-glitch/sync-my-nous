import sqlite3
import json
import os
import time

DB_PATH = "data/nous_storage.db"

def _get_connection():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = _get_connection()
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                data TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_timestamp ON memories(timestamp)
        """)
    conn.close()

init_db()

def save_memory(entry: dict):
    conn = _get_connection()
    with conn:
        conn.execute(
            "INSERT INTO memories (timestamp, data) VALUES (?, ?)",
            (time.time(), json.dumps(entry, ensure_ascii=False))
        )
        # Keep last 500 records
        conn.execute("""
            DELETE FROM memories WHERE id NOT IN (
                SELECT id FROM memories ORDER BY id DESC LIMIT 500
            )
        """)
    conn.close()

def load_memories(limit=200) -> list[dict]:
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("SELECT data FROM memories ORDER BY id ASC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    result = []
    for row in rows:
        try:
            result.append(json.loads(row["data"]))
        except Exception:
            pass
    return result
