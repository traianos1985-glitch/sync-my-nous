"""User-scoped persistent memory backed by Neon/Postgres."""
from __future__ import annotations

import json
import os
import uuid
from typing import Any, TypeVar

import psycopg

T = TypeVar("T")
ENTRY_PREFIX = "entry:"
MAX_ENTRIES = 500
MIGRATION_KEY = "__nous_sqlite_memory_migration_v1__"


def _connection():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is required for persistent memory")
    return psycopg.connect(url)


def load(user_id: str = "default") -> dict[str, Any]:
    with _connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT memory_key, value FROM nous_memory_entries WHERE user_id = %s",
            (user_id,),
        )
        return {key: value for key, value in cur.fetchall()}


def save(data: dict[str, Any], user_id: str = "default") -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("memory_data_must_be_object")
    with _connection() as conn, conn.cursor() as cur:
        for key, value in data.items():
            cur.execute(
                """INSERT INTO nous_memory_entries (id, user_id, memory_key, value, updated_at)
                   VALUES (%s, %s, %s, %s::jsonb, now())
                   ON CONFLICT (user_id, memory_key)
                   DO UPDATE SET value = EXCLUDED.value, updated_at = now()""",
                (str(uuid.uuid4()), user_id, key, json.dumps(value, ensure_ascii=False, allow_nan=False)),
            )
    return data


def set_mem(key: str, value: Any, user_id: str = "default") -> dict[str, Any]:
    return save({key: value}, user_id)


def get_mem(key: str, default: T = None, user_id: str = "default") -> T:
    with _connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT value FROM nous_memory_entries WHERE user_id = %s AND memory_key = %s LIMIT 1",
            (user_id, key),
        )
        row = cur.fetchone()
    value = row[0] if row else default
    return value  # type: ignore[return-value]


def append_entry(entry: dict[str, Any], user_id: str = "default") -> str:
    """Append one immutable memory event; concurrent installations cannot overwrite each other."""
    if not isinstance(entry, dict):
        raise ValueError("memory_entry_must_be_object")
    key = f"{ENTRY_PREFIX}{uuid.uuid4()}"
    encoded = json.dumps(entry, ensure_ascii=False, allow_nan=False)
    with _connection() as conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO nous_memory_entries (id, user_id, memory_key, value, updated_at)
               VALUES (%s, %s, %s, %s::jsonb, now())""",
            (str(uuid.uuid4()), user_id, key, encoded),
        )
        # Keep the event log bounded without affecting key/value metadata.
        cur.execute(
            """DELETE FROM nous_memory_entries
               WHERE user_id = %s
                 AND memory_key LIKE 'entry:%%'
                 AND memory_key NOT IN (
                     SELECT memory_key FROM nous_memory_entries
                     WHERE user_id = %s AND memory_key LIKE 'entry:%%'
                     ORDER BY created_at DESC, memory_key DESC
                     LIMIT %s
                 )""",
            (user_id, user_id, MAX_ENTRIES),
        )
    return key


def load_entries(user_id: str = "default", limit: int = MAX_ENTRIES) -> list[dict[str, Any]]:
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("memory_limit_must_be_positive_integer")
    limit = min(limit, MAX_ENTRIES)
    with _connection() as conn, conn.cursor() as cur:
        cur.execute(
            """SELECT value FROM (
                   SELECT memory_key, value, created_at
                   FROM nous_memory_entries
                   WHERE user_id = %s AND memory_key LIKE 'entry:%%'
                   ORDER BY created_at DESC, memory_key DESC
                   LIMIT %s
               ) AS recent
               ORDER BY created_at ASC, memory_key ASC""",
            (user_id, limit),
        )
        rows = cur.fetchall()
    result = []
    for (value,) in rows:
        if not isinstance(value, dict):
            raise RuntimeError("memory_store_integrity_failure:record_shape")
        result.append(value)
    return result
