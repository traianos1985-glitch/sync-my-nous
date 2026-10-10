import importlib
import json
import sqlite3
from pathlib import Path

import pytest


def _modules(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from executor import sqlite_store, memory
    store = importlib.reload(sqlite_store)
    monkeypatch.setattr(store, "DB_PATH", "data/test_memory.db")
    facade = importlib.reload(memory)
    return store, facade


def test_memory_load_returns_newest_records_in_chronological_order(tmp_path, monkeypatch):
    store, _ = _modules(tmp_path, monkeypatch)
    for number in range(1, 8):
        store.save_memory({"number": number})

    assert store.load_memories(limit=3) == [
        {"number": 5}, {"number": 6}, {"number": 7}
    ]
    assert len(store.load_memories(limit=9999)) == 7


@pytest.mark.parametrize("limit", [0, -1, True, 1.5, "2", None])
def test_memory_limit_must_be_a_positive_integer(tmp_path, monkeypatch, limit):
    store, _ = _modules(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="memory_limit_must_be_positive_integer"):
        store.load_memories(limit=limit)


def test_corrupt_sqlite_memory_record_fails_closed(tmp_path, monkeypatch):
    store, _ = _modules(tmp_path, monkeypatch)
    store.save_memory({"safe": True})
    conn = sqlite3.connect(store.DB_PATH)
    try:
        conn.execute("INSERT INTO memories (timestamp, data) VALUES (?, ?)", (1.0, "{broken"))
        conn.commit()
    finally:
        conn.close()

    with pytest.raises(RuntimeError, match="memory_store_integrity_failure"):
        store.load_memories()


def test_memory_facade_does_not_hide_sqlite_failure_or_corrupt_mirror(tmp_path, monkeypatch):
    store, facade = _modules(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="memory_entry_must_be_object"):
        facade.save(["not", "an", "object"])

    Path("data").mkdir(exist_ok=True)
    Path(facade.MEMORY_FILE).write_text('{"wrong":"shape"}', encoding="utf-8")
    with pytest.raises(RuntimeError, match="json_state_integrity_failure"):
        facade.load()


def test_memory_save_keeps_sqlite_and_legacy_mirror_consistent(tmp_path, monkeypatch):
    store, facade = _modules(tmp_path, monkeypatch)
    facade.save({"event": "first"})
    facade.save({"event": "second"})

    assert store.load_memories() == [{"event": "first"}, {"event": "second"}]
    assert json.loads(Path(facade.MEMORY_FILE).read_text(encoding="utf-8")) == [
        {"event": "first"}, {"event": "second"}
    ]
