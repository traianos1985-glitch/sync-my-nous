"""User-scoped persistent memory backed by Neon/Postgres."""
from __future__ import annotations

import json
import os
import uuid
from typing import Any, TypeVar

import psycopg

T = TypeVar("T")


def _connection():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is required for persistent memory")
    return psycopg.connect(url)


def load(user_id: str = "default") -> dict[str, Any]:
    with _connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT memory_key, value FROM nous_memory_entries WHERE user_id = %s", (user_id,))
        return {key: value for key, value in cur.fetchall()}


def save(data: dict[str, Any], user_id: str = "default") -> dict[str, Any]:
    with _connection() as conn, conn.cursor() as cur:
        for key, value in data.items():
            cur.execute(
                """INSERT INTO nous_memory_entries (id, user_id, memory_key, value, updated_at)
                   VALUES (%s, %s, %s, %s::jsonb, now())
                   ON CONFLICT (user_id, memory_key)
                   DO UPDATE SET value = EXCLUDED.value, updated_at = now()""",
                (str(uuid.uuid4()), user_id, key, json.dumps(value, ensure_ascii=False)),
            )
    return data


def set_mem(key: str, value: Any, user_id: str = "default") -> dict[str, Any]:
    return save({key: value}, user_id)


def get_mem(key: str, default: T = None, user_id: str = "default") -> T:
    value = load(user_id).get(key, default)
    return value  # type: ignore[return-value]
