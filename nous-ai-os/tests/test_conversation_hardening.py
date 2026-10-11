from pathlib import Path

import pytest

from executor import conversation_manager as manager
from executor import conversation_search_engine as search_engine
from executor import conversation_title_engine as title_engine


def isolate_storage(tmp_path, monkeypatch):
    conv_dir = tmp_path / "conversations"
    index = tmp_path / "conversation_index.json"
    reports = tmp_path / "reports"
    monkeypatch.setattr(manager, "CONV_DIR", conv_dir)
    monkeypatch.setattr(manager, "INDEX", index)
    monkeypatch.setattr(search_engine, "INDEX", index)
    monkeypatch.setattr(search_engine, "REPORTS", reports)
    monkeypatch.setattr(title_engine, "INDEX", index)
    return conv_dir, index, reports


def test_corrupt_index_is_preserved_and_new_conversation_is_not_written(tmp_path, monkeypatch):
    conv_dir, index, _ = isolate_storage(tmp_path, monkeypatch)
    index.write_text('{"unexpected": "object"}', encoding="utf-8")
    original = index.read_bytes()
    with pytest.raises(ValueError, match="Invalid conversation index structure"):
        manager.new_conversation("Should not be created")
    assert index.read_bytes() == original
    assert not list(conv_dir.glob("*.json"))


def test_index_mutations_fail_closed_on_wrong_json_shape(tmp_path, monkeypatch):
    _, index, _ = isolate_storage(tmp_path, monkeypatch)
    original = b'{"unexpected": "object"}'
    index.write_bytes(original)
    with pytest.raises(ValueError, match="Invalid conversation index structure"):
        manager.update_index({"id": "123", "messages": []})
    with pytest.raises(ValueError, match="Invalid conversation index structure"):
        manager.delete_conversation("123")
    assert index.read_bytes() == original


def test_listing_limits_are_bounded_and_invalid_values_do_not_raise(tmp_path, monkeypatch):
    isolate_storage(tmp_path, monkeypatch)
    for n in range(25):
        manager.append_turn(f"topic {n}", f"answer {n}")
    assert len(manager.list_conversations(100000)["conversations"]) == 25
    assert len(manager.list_conversations("invalid")["conversations"]) == 25
    assert len(manager.list_conversations(-5)["conversations"]) == 1


def test_search_rejects_oversized_queries_and_bounds_limit(tmp_path, monkeypatch):
    isolate_storage(tmp_path, monkeypatch)
    manager.append_turn("Larmor measurement log", "Frequency notes")
    assert search_engine.search_conversations("x" * 501)["error"] == "query_too_long"
    result = search_engine.search_conversations("Larmor", limit=100000, write_report=False)
    assert result["ok"] is True and len(result["hits"]) == 1
    assert search_engine.search_conversations("Larmor", limit="invalid", write_report=False)["ok"] is True


def test_cross_conversation_context_does_not_write_reports(tmp_path, monkeypatch):
    _, _, reports = isolate_storage(tmp_path, monkeypatch)
    manager.append_turn("Larmor field measurements", "Recorded the measurements")
    assert "Larmor" in search_engine.cross_conversation_context("Larmor")
    assert not reports.exists()


def test_explicit_search_reports_have_unique_names(tmp_path, monkeypatch):
    _, _, reports = isolate_storage(tmp_path, monkeypatch)
    manager.append_turn("Larmor field measurements", "Recorded the measurements")
    first = search_engine.search_conversations("Larmor")
    second = search_engine.search_conversations("Larmor")
    assert first["report_path"] != second["report_path"]
    assert Path(first["report_path"]).exists() and Path(second["report_path"]).exists()


def test_auto_title_limit_and_corrupt_index_handling(tmp_path, monkeypatch):
    _, index, _ = isolate_storage(tmp_path, monkeypatch)
    manager.append_turn("Σημείωσε ότι πρέπει να δοκιμάσουμε Larmor", "Καταγράφηκε")
    assert title_engine.auto_title_recent_conversations("invalid")["ok"] is True
    original = b'{"unexpected": "object"}'
    index.write_bytes(original)
    with pytest.raises(ValueError, match="Invalid conversation index structure"):
        title_engine.auto_title_recent_conversations()
    assert index.read_bytes() == original
