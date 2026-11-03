"""Shared transcript persistence tests using an isolated state adapter."""

from contextlib import contextmanager
from copy import deepcopy

from executor import conversation_manager as manager
from executor import shared_state_store


def test_conversation_turns_append_without_lost_updates_in_cloud_mode(monkeypatch, tmp_path):
    documents = {}
    monkeypatch.setattr(shared_state_store, "cloud_enabled", lambda: True)
    monkeypatch.setattr(manager, "CONV_DIR", tmp_path / "conversations")
    monkeypatch.setattr(manager, "INDEX", tmp_path / "conversation_index.json")

    @contextmanager
    def edit(path, default):
        key = str(path)
        if key not in documents:
            documents[key] = deepcopy(default)
        yield documents[key]

    def read(path, default):
        return documents.get(str(path), deepcopy(default))

    def write(path, value):
        documents[str(path)] = deepcopy(value)
        return value

    monkeypatch.setattr(shared_state_store, "edit_state", edit)
    monkeypatch.setattr(shared_state_store, "read_state", read)
    monkeypatch.setattr(shared_state_store, "write_state", write)

    first = manager.append_turn("Πρώτο", "Απάντηση 1", title="Shared")
    second = manager.append_turn("Δεύτερο", "Απάντηση 2", conversation_id=first["conversation_id"])

    conversation = manager.get_conversation(first["conversation_id"])
    assert second["conversation_id"] == first["conversation_id"]
    assert [item["content"] for item in conversation["messages"]] == [
        "Πρώτο", "Απάντηση 1", "Δεύτερο", "Απάντηση 2"
    ]
    assert manager.list_conversations()["conversations"][0]["messages"] == 4


def test_conversation_delete_uses_cloud_tombstone(monkeypatch, tmp_path):
    documents = {}
    monkeypatch.setattr(shared_state_store, "cloud_enabled", lambda: True)
    monkeypatch.setattr(manager, "CONV_DIR", tmp_path / "conversations")
    monkeypatch.setattr(manager, "INDEX", tmp_path / "conversation_index.json")

    @contextmanager
    def edit(path, default):
        key = str(path)
        if key not in documents:
            documents[key] = deepcopy(default)
        yield documents[key]

    monkeypatch.setattr(shared_state_store, "edit_state", edit)
    monkeypatch.setattr(shared_state_store, "read_state", lambda path, default: documents.get(str(path), deepcopy(default)))
    monkeypatch.setattr(shared_state_store, "write_state", lambda path, value: documents.__setitem__(str(path), deepcopy(value)) or value)

    created = manager.new_conversation("To delete")
    result = manager.delete_conversation(created["id"])

    assert result["ok"] is True
    assert manager.get_conversation(created["id"])["error"] == "conversation_not_found"
    assert documents[str(manager.CONV_DIR / f"{created['id']}.json")]["deleted"] is True
