"""Integration contracts for JSON-backed memory stores in Neon mode."""

from contextlib import contextmanager

from executor import json_object_store, json_state_store, shared_state_store


def test_list_store_uses_transactional_shared_document(monkeypatch):
    state = []
    monkeypatch.setattr(shared_state_store, "cloud_enabled", lambda: True)

    @contextmanager
    def edit(path, default):
        assert path == "data/lessons.json"
        assert default == []
        yield state

    monkeypatch.setattr(shared_state_store, "edit_state", edit)
    monkeypatch.setattr(shared_state_store, "read_state", lambda path, default: list(state))
    monkeypatch.setattr(shared_state_store, "write_state", lambda path, value: state.__setitem__(slice(None), value))

    with json_state_store.edit_list("data/lessons.json") as items:
        items.append({"lesson": "shared"})
    assert json_state_store.read_list("data/lessons.json") == [{"lesson": "shared"}]


def test_object_store_uses_transactional_shared_document(monkeypatch):
    state = {"profile": {}, "goals": [], "projects": [], "decisions": []}
    monkeypatch.setattr(shared_state_store, "cloud_enabled", lambda: True)

    @contextmanager
    def edit(path, default):
        assert path == "data/personal_agent.json"
        yield state

    monkeypatch.setattr(shared_state_store, "edit_state", edit)
    monkeypatch.setattr(shared_state_store, "read_state", lambda path, default: state)

    with json_object_store.edit_object("data/personal_agent.json") as value:
        value["profile"]["fact"] = "visible across installs"

    assert json_object_store.read_object("data/personal_agent.json")["profile"]["fact"] == "visible across installs"


def test_list_and_object_validation_remains_fail_closed(monkeypatch):
    monkeypatch.setattr(shared_state_store, "cloud_enabled", lambda: True)
    monkeypatch.setattr(shared_state_store, "read_state", lambda path, default: ["bad-shape"])

    import pytest

    with pytest.raises(RuntimeError, match="json_state_integrity_failure"):
        json_state_store.read_list("data/lessons.json")

    monkeypatch.setattr(shared_state_store, "read_state", lambda path, default: {"profile": [], "goals": [], "projects": [], "decisions": []})
    with pytest.raises(RuntimeError, match="json_state_integrity_failure"):
        json_object_store.read_object("data/personal_agent.json")
