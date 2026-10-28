"""Transactional runtime snapshots and claims in the shared SQLite database.

Legacy JSON is imported once, validated, and left untouched as a backup.
The transaction spans read/modify/write, never external action execution.
"""
import json
import os
import sqlite3
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

_connections = ContextVar("runtime_store_connections", default=None)


def database_path(legacy_file):
    return os.environ.get("NOUS_DB_PATH") or str(Path(legacy_file).parent / "nous_storage.db")


@contextmanager
def transaction(legacy_file, error_prefix):
    key = str(Path(legacy_file).resolve())
    active = _connections.get() or {}
    if key in active:
        yield
        return
    path = database_path(legacy_file)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=15)
    conn.execute("PRAGMA busy_timeout = 15000")
    conn.execute("PRAGMA synchronous = FULL")
    token = None
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("CREATE TABLE IF NOT EXISTS runtime_snapshots (namespace TEXT PRIMARY KEY, data TEXT NOT NULL)")
        conn.execute("CREATE TABLE IF NOT EXISTS task_claims (namespace TEXT NOT NULL, mission_id TEXT NOT NULL, task_id TEXT NOT NULL, execution_id TEXT NOT NULL, status TEXT NOT NULL, started REAL, PRIMARY KEY(namespace, mission_id, task_id))")
        token = _connections.set({**active, key: conn})
        if conn.execute("SELECT 1 FROM runtime_snapshots WHERE namespace=?", (key,)).fetchone() is None:
            items = []
            if Path(legacy_file).exists():
                try:
                    items = json.loads(Path(legacy_file).read_text(encoding="utf-8"))
                except (OSError, ValueError, UnicodeError) as exc:
                    raise RuntimeError(error_prefix) from exc
                if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
                    raise RuntimeError(error_prefix)
            save(legacy_file, items)
        yield
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        if token is not None:
            _connections.reset(token)
        conn.close()


def load(legacy_file):
    key = str(Path(legacy_file).resolve())
    conn = (_connections.get() or {})[key]
    row = conn.execute("SELECT data FROM runtime_snapshots WHERE namespace=?", (key,)).fetchone()
    try:
        items = json.loads(row[0])
    except (TypeError, ValueError) as exc:
        raise RuntimeError("runtime_store_integrity_failure") from exc
    if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
        raise RuntimeError("runtime_store_integrity_failure")
    return items


def save(legacy_file, items):
    if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
        raise RuntimeError("runtime_store_integrity_failure")
    key = str(Path(legacy_file).resolve())
    conn = (_connections.get() or {})[key]
    encoded = json.dumps(items, ensure_ascii=False, allow_nan=False)
    conn.execute("INSERT INTO runtime_snapshots(namespace,data) VALUES(?,?) ON CONFLICT(namespace) DO UPDATE SET data=excluded.data", (key, encoded))
    conn.execute("DELETE FROM task_claims WHERE namespace=?", (key,))
    for mission in items:
        tasks = mission.get("tasks", [])
        if not isinstance(tasks, list):
            continue
        for task in tasks:
            if isinstance(task, dict) and task.get("execution_id"):
                conn.execute("INSERT INTO task_claims VALUES(?,?,?,?,?,?)", (key, str(mission.get("id")), str(task.get("id")), str(task["execution_id"]), str(task.get("status")), task.get("started")))