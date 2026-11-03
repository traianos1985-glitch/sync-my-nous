from contextlib import contextmanager
import importlib

import pytest


def _fake_store(monkeypatch, store_module):
    values = {}
    entries = []
    calls = {"append": 0, "migration_writes": 0}

    def get_mem(key, default=None, user_id="default"):
        return values.get((user_id, key), default)

    def set_mem(key, value, user_id="default"):
        values[(user_id, key)] = value
        if key.startswith(store_module.ENTRY_PREFIX):
            entries.append(value)
            calls["migration_writes"] += 1
        return {key: value}

    def save(data, user_id="default"):
        for key, value in data.items():
            values[(user_id, key)] = value
            if key.startswith(store_module.ENTRY_PREFIX):
                entries.append(value)
                calls["migration_writes"] += 1
        return data

    def append_entry(entry, user_id="default"):
        calls["append"] += 1
        entries.append(entry)
        return f"{store_module.ENTRY_PREFIX}test-{calls['append']}"

    def load_entries(user_id="default", limit=store_module.MAX_ENTRIES):
        return entries[-limit:]

    monkeypatch.setattr(store_module, "get_mem", get_mem)
    monkeypatch.setattr(store_module, "set_mem", set_mem)
    monkeypatch.setattr(store_module, "save", save)
    monkeypatch.setattr(store_module, "append_entry", append_entry)
    monkeypatch.setattr(store_module, "load_entries", load_entries)
    return values, entries, calls


def test_neon_memory_migrates_legacy_sqlite_once(monkeypatch):
    from executor import memory_store, sqlite_store
    import executor.memory as memory

    monkeypatch.setenv("DATABASE_URL", "postgresql://test.invalid/db")
    monkeypatch.setenv("NOUS_TOKEN", "test-owner-token")
    values, entries, calls = _fake_store(monkeypatch, memory_store)
    legacy = [{"text": "old one"}, {"text": "old two"}]
    monkeypatch.setattr(sqlite_store, "load_memories", lambda limit=200: legacy)

    facade = importlib.reload(memory)
    assert facade.load() == legacy
    assert calls["migration_writes"] == 2
    assert facade.load() == legacy
    assert calls["migration_writes"] == 2
    assert memory_store.MIGRATION_KEY in {
        key for (user_id, key) in values
    }


def test_neon_memory_appends_without_overwriting_other_installation_entries(monkeypatch):
    from executor import memory_store, sqlite_store
    import executor.memory as memory

    monkeypatch.setenv("DATABASE_URL", "postgresql://test.invalid/db")
    monkeypatch.setenv("NOUS_TOKEN", "test-owner-token")
    _, entries, calls = _fake_store(monkeypatch, memory_store)
    monkeypatch.setattr(sqlite_store, "load_memories", lambda limit=200: [])

    @contextmanager
    def fake_edit_list(_path):
        yield []

    monkeypatch.setattr(memory, "edit_list", fake_edit_list)
    facade = importlib.reload(memory)
    monkeypatch.setattr(facade, "save_memory", lambda entry: None)

    first = {"message": "from installation A"}
    second = {"message": "from installation B"}
    assert facade.save(first) == {"ok": True, "postgres": True, "sqlite_mirror": True}
    assert facade.save(second) == {"ok": True, "postgres": True, "sqlite_mirror": True}
    assert calls["append"] == 2
    assert entries == [first, second]


def test_neon_memory_does_not_claim_success_when_postgres_write_fails(monkeypatch):
    from executor import memory_store, sqlite_store
    import executor.memory as memory

    monkeypatch.setenv("DATABASE_URL", "postgresql://test.invalid/db")
    monkeypatch.setenv("NOUS_TOKEN", "test-owner-token")
    _fake_store(monkeypatch, memory_store)
    monkeypatch.setattr(sqlite_store, "load_memories", lambda limit=200: [])
    monkeypatch.setattr(
        memory_store,
        "append_entry",
        lambda entry, user_id="default": (_ for _ in ()).throw(RuntimeError("db unavailable")),
    )

    facade = importlib.reload(memory)
    with pytest.raises(RuntimeError, match="db unavailable"):
        facade.save({"message": "must not report local-only success"})


def test_neon_memory_user_scope_is_derived_from_token_without_exposing_it(monkeypatch):
    import executor.memory as memory

    monkeypatch.delenv("NOUS_MEMORY_USER_ID", raising=False)
    monkeypatch.setenv("NOUS_TOKEN", "owner-secret-token")
    facade = importlib.reload(memory)
    first = facade._postgres_user_id()
    assert first.startswith("token:")
    assert "owner-secret-token" not in first
    monkeypatch.setenv("NOUS_TOKEN", "different-token")
    assert facade._postgres_user_id() != first
