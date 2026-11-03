"""Compatibility facade for persistent memory.

When DATABASE_URL is configured, Neon is authoritative and SQLite remains a
best-effort local mirror. Without DATABASE_URL, the existing SQLite + JSON
behavior is preserved for standalone/mobile installations.
"""
from __future__ import annotations

import hashlib
import json
import os

from executor.sqlite_store import save_memory, load_memories
from executor.json_state_store import edit_list, read_list

MEMORY_FILE = "data/memory.json"
MAX_MEMORIES = 500


def _postgres_user_id() -> str:
    configured = os.environ.get("NOUS_MEMORY_USER_ID", "").strip()
    if configured:
        return configured
    token = os.environ.get("NOUS_TOKEN", "").strip()
    if token:
        return "token:" + hashlib.sha256(token.encode("utf-8")).hexdigest()[:32]
    return "default"


def _migrate_sqlite_once(store, user_id: str) -> None:
    """Import the existing local history once; stable keys make retries safe."""
    marker = store.get_mem(store.MIGRATION_KEY, None, user_id=user_id)
    if marker is not None:
        return
    legacy = load_memories(limit=store.MAX_ENTRIES)
    migration_batch = {}
    for index, entry in enumerate(legacy):
        canonical = json.dumps(entry, sort_keys=True, ensure_ascii=False, allow_nan=False)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
        migration_batch[f"{store.ENTRY_PREFIX}legacy:{index:06d}:{digest}"] = entry
    migration_batch[store.MIGRATION_KEY] = {
        "version": 1,
        "imported": len(legacy),
    }
    # One transaction/connection: if interrupted, the marker and imported rows
    # roll back together, so the next startup can safely retry the migration.
    store.save(migration_batch, user_id=user_id)


def load():
    if os.environ.get("DATABASE_URL"):
        from executor import memory_store

        user_id = _postgres_user_id()
        _migrate_sqlite_once(memory_store, user_id)
        return memory_store.load_entries(user_id=user_id, limit=MAX_MEMORIES)

    # SQLite is authoritative whenever it contains records. Integrity failures
    # propagate instead of being hidden by an older, potentially stale mirror.
    memories = load_memories()
    if memories:
        return memories
    return read_list(MEMORY_FILE)


def save(entry):
    if not isinstance(entry, dict):
        raise ValueError("memory_entry_must_be_object")

    if os.environ.get("DATABASE_URL"):
        from executor import memory_store

        user_id = _postgres_user_id()
        _migrate_sqlite_once(memory_store, user_id)
        # Postgres append is the authoritative write. A DB failure propagates;
        # we never claim a cloud-synced save when Neon did not accept it.
        memory_store.append_entry(entry, user_id=user_id)
        mirror = True
        try:
            # Keep the legacy SQLite mirror for standalone recovery. The JSON
            # document adapter is cloud-aware, so do not route this local mirror
            # write back into the shared Neon document namespace.
            save_memory(entry)
        except Exception:
            mirror = False
        return {"ok": True, "postgres": True, "sqlite_mirror": mirror}

    # Standalone/mobile mode retains its established local persistence behavior.
    save_memory(entry)
    with edit_list(MEMORY_FILE) as memories:
        memories.append(entry)
        del memories[:-200]
    return {"ok": True, "sqlite": True, "legacy_mirror": True}
