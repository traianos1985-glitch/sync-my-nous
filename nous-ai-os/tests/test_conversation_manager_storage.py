from pathlib import Path

import pytest

from executor import conversation_manager as manager


def test_load_json_returns_default_only_when_file_is_missing(tmp_path: Path):
    path = tmp_path / "missing.json"
    default = {"fallback": True}

    assert manager.load_json(path, default) is default


def test_load_json_reports_corruption_without_overwriting_file(tmp_path: Path):
    path = tmp_path / "conversation.json"
    original = b'{"messages": ['
    path.write_bytes(original)

    with pytest.raises(ValueError, match="Invalid JSON"):
        manager.load_json(path, {})

    assert path.read_bytes() == original


def test_save_json_atomically_replaces_file_and_cleans_temporary_files(tmp_path: Path):
    path = tmp_path / "nested" / "state.json"
    path.parent.mkdir()
    path.write_text('{"old": true}', encoding="utf-8")

    manager.save_json(path, {"title": "ΝΟΥΣ", "messages": [1, 2]})

    assert manager.load_json(path, None) == {"title": "ΝΟΥΣ", "messages": [1, 2]}
    assert list(path.parent.glob(".state.json.*.tmp")) == []


def test_conversation_turn_persists_to_conversation_and_index(tmp_path: Path, monkeypatch):
    conversation_dir = tmp_path / "conversations"
    index_path = tmp_path / "conversation_index.json"
    monkeypatch.setattr(manager, "CONV_DIR", conversation_dir)
    monkeypatch.setattr(manager, "INDEX", index_path)

    result = manager.append_turn("Γεια", "Καλησπέρα", title="Δοκιμή")

    conversation = manager.get_conversation(result["conversation_id"])
    listing = manager.list_conversations()

    assert conversation["messages"][0]["content"] == "Γεια"
    assert conversation["messages"][1]["content"] == "Καλησπέρα"
    assert listing["conversations"][0]["id"] == result["conversation_id"]
