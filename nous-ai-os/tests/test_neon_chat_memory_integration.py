"""Neon integration for the chat context memory path."""

import pytest


def test_chat_memory_migrates_legacy_file_once_to_neon(monkeypatch):
    from executor import memory as persistent_memory
    from executor import memory_store
    import executor.chat_brain_v3 as brain

    monkeypatch.setenv("DATABASE_URL", "postgresql://test.invalid/db")
    legacy = [
        {"time": "2026-01-01T00:00:00Z", "user": "old question", "answer": "old answer", "mode": "chat"}
    ]
    values = {}
    entries = []
    writes = []

    monkeypatch.setattr(brain, "load_json", lambda path, default: legacy if path == brain.CHAT_MEMORY else default)
    monkeypatch.setattr(persistent_memory, "_postgres_user_id", lambda: "token:test-user")
    monkeypatch.setattr(persistent_memory, "load", lambda: list(entries))

    def get_mem(key, default=None, user_id="default"):
        return values.get((user_id, key), default)

    def save(data, user_id="default"):
        writes.append(dict(data))
        for key, value in data.items():
            values[(user_id, key)] = value
            if key.startswith(memory_store.ENTRY_PREFIX):
                entries.append(value)
        return data

    monkeypatch.setattr(memory_store, "get_mem", get_mem)
    monkeypatch.setattr(memory_store, "save", save)

    assert brain.load_chat_memory() == legacy
    assert len(writes) == 1
    assert writes[0][brain.CHAT_MEMORY_MIGRATION_KEY]["imported"] == 1

    assert brain.load_chat_memory() == legacy
    assert len(writes) == 1


def test_remember_turn_writes_shared_memory_and_keeps_local_recovery_mirror(monkeypatch):
    from executor import memory as persistent_memory
    import executor.chat_brain_v3 as brain

    monkeypatch.setenv("DATABASE_URL", "postgresql://test.invalid/db")
    local = []
    calls = []
    monkeypatch.setattr(brain, "load_chat_memory", lambda: [])
    monkeypatch.setattr(brain, "load_json", lambda path, default: list(local) if path == brain.CHAT_MEMORY else default)
    monkeypatch.setattr(brain, "save_json", lambda path, data: local.__setitem__(slice(None), list(data)))
    monkeypatch.setattr(
        persistent_memory,
        "save",
        lambda entry: calls.append(dict(entry)) or {"ok": True, "postgres": True, "sqlite_mirror": True},
    )

    result = brain.remember_turn("new question", "new answer", "chat")

    assert result["postgres"] is True
    assert len(calls) == 1
    assert calls[0]["user"] == "new question"
    assert calls[0]["answer"] == "new answer"
    assert local == calls


def test_remember_turn_preserves_local_copy_if_neon_write_fails(monkeypatch):
    from executor import memory as persistent_memory
    import executor.chat_brain_v3 as brain

    monkeypatch.setenv("DATABASE_URL", "postgresql://test.invalid/db")
    local = []
    monkeypatch.setattr(brain, "load_chat_memory", lambda: [])
    monkeypatch.setattr(brain, "load_json", lambda path, default: list(local) if path == brain.CHAT_MEMORY else default)
    monkeypatch.setattr(brain, "save_json", lambda path, data: local.__setitem__(slice(None), list(data)))

    def fail(_entry):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(persistent_memory, "save", fail)

    with pytest.raises(RuntimeError, match="database unavailable"):
        brain.remember_turn("question", "answer", "chat")

    assert len(local) == 1
    assert local[0]["user"] == "question"
