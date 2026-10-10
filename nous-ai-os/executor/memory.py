"""Compatibility facade for SQLite memory and the legacy JSON mirror."""
from executor.sqlite_store import save_memory, load_memories
from executor.json_state_store import edit_list, read_list

MEMORY_FILE = "data/memory.json"


def load():
    # SQLite is authoritative whenever it contains records. Integrity failures
    # propagate instead of being hidden by an older, potentially stale mirror.
    memories = load_memories()
    if memories:
        return memories
    return read_list(MEMORY_FILE)


def save(entry):
    if not isinstance(entry, dict):
        raise ValueError("memory_entry_must_be_object")

    # Persist to the primary store first. If this fails, don't report a successful
    # save or silently fall back to a potentially divergent copy.
    save_memory(entry)
    with edit_list(MEMORY_FILE) as memories:
        memories.append(entry)
        del memories[:-200]
    return {"ok": True, "sqlite": True, "legacy_mirror": True}
