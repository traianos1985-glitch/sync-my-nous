"""Transactional, per-NOUS-user JSON state documents backed by Neon.

The existing JSON files remain the offline/local fallback and are imported
lazily on first cloud access. Each document is protected by a PostgreSQL
transaction-scoped advisory lock, so read/modify/write operations from several
installations cannot overwrite one another.
"""
from __future__ import annotations

import hashlib
import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import psycopg


def cloud_enabled() -> bool:
    return bool(os.environ.get("DATABASE_URL", "").strip())


def user_id() -> str:
    configured = os.environ.get("NOUS_MEMORY_USER_ID", "").strip()
    if configured:
        return configured
    token = os.environ.get("NOUS_TOKEN", "").strip()
    if token:
        return "token:" + hashlib.sha256(token.encode("utf-8")).hexdigest()[:32]
    return "default"


def _identity(path: str | Path) -> tuple[str, str]:
    normalized = str(Path(path)).replace("\\", "/").lstrip("./")
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:32]
    return user_id(), "state:" + digest


def _read_legacy(path: str | Path, default: Any) -> Any:
    target = Path(path)
    if not target.exists():
        return default
    try:
        value = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("shared_state_legacy_integrity_failure") from exc
    return value


def _lock(cur, uid: str, key: str) -> None:
    cur.execute(
        "SELECT pg_advisory_xact_lock(hashtext(%s), hashtext(%s))",
        (uid, key),
    )


def _get_or_import(cur, uid: str, key: str, path: str | Path, default: Any) -> Any:
    cur.execute(
        "SELECT value FROM nous_memory_entries WHERE user_id = %s AND memory_key = %s",
        (uid, key),
    )
    row = cur.fetchone()
    if row:
        return row[0]
    legacy = _read_legacy(path, default)
    if Path(path).exists():
        _put(cur, uid, key, legacy)
    return legacy


def _put(cur, uid: str, key: str, value: Any) -> None:
    encoded = json.dumps(value, ensure_ascii=False, allow_nan=False)
    cur.execute(
        """INSERT INTO nous_memory_entries (id, user_id, memory_key, value, updated_at)
           VALUES (%s, %s, %s, %s::jsonb, now())
           ON CONFLICT (user_id, memory_key)
           DO UPDATE SET value = EXCLUDED.value, updated_at = now()""",
        (hashlib.sha256((uid + key).encode()).hexdigest(), uid, key, encoded),
    )


def read_state(path: str | Path, default: Any) -> Any:
    uid, key = _identity(path)
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn, conn.cursor() as cur:
        _lock(cur, uid, key)
        return _get_or_import(cur, uid, key, path, default)


def write_state(path: str | Path, value: Any) -> Any:
    uid, key = _identity(path)
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn, conn.cursor() as cur:
        _lock(cur, uid, key)
        _put(cur, uid, key, value)
    return value


@contextmanager
def edit_state(path: str | Path, default: Any) -> Iterator[Any]:
    """Yield a document while holding its DB lock; commit only on clean exit."""
    uid, key = _identity(path)
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn, conn.cursor() as cur:
        _lock(cur, uid, key)
        value = _get_or_import(cur, uid, key, path, default)
        yield value
        _put(cur, uid, key, value)
