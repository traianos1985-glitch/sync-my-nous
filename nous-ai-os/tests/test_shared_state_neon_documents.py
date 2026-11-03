"""Tests for transactional, user-scoped shared JSON state documents."""

import json

import pytest

from executor import shared_state_store


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection
        self.row = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, sql, params=()):
        if sql.lstrip().startswith("SELECT value FROM nous_memory_entries"):
            self.row = self.connection.values.get((params[0], params[1]))
        elif sql.lstrip().startswith("INSERT INTO nous_memory_entries"):
            _row_id, uid, key, encoded = params
            self.connection.values[(uid, key)] = json.loads(encoded)
        elif "pg_advisory_xact_lock" in sql:
            return None

    def fetchone(self):
        return (self.row,) if self.row is not None else None


class FakeConnection:
    def __init__(self, values):
        self.values = values
        self.before = dict(values)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, *_args):
        if exc_type:
            self.values.clear()
            self.values.update(self.before)
        return False

    def cursor(self):
        return FakeCursor(self)


def install_fake_database(monkeypatch):
    values = {}
    monkeypatch.setattr(
        shared_state_store.psycopg,
        "connect",
        lambda _url: FakeConnection(values),
    )
    monkeypatch.setenv("DATABASE_URL", "postgresql://test.invalid/db")
    return values


def test_state_is_scoped_by_hashed_nous_token(monkeypatch, tmp_path):
    install_fake_database(monkeypatch)
    path = tmp_path / "profile.json"

    monkeypatch.setenv("NOUS_TOKEN", "same-owner-token")
    shared_state_store.write_state(path, {"profile": {"fact": "shared"}})
    first = shared_state_store.read_state(path, {})

    monkeypatch.setenv("NOUS_TOKEN", "another-owner-token")
    second = shared_state_store.read_state(path, {})

    assert first == {"profile": {"fact": "shared"}}
    assert second == {}


def test_legacy_json_is_imported_once_and_cloud_becomes_authoritative(monkeypatch, tmp_path):
    install_fake_database(monkeypatch)
    path = tmp_path / "legacy.json"
    path.write_text('{"items": [1, 2]}', encoding="utf-8")

    first = shared_state_store.read_state(path, {})
    path.write_text('{"items": ["stale-local-copy"]}', encoding="utf-8")
    second = shared_state_store.read_state(path, {})

    assert first == {"items": [1, 2]}
    assert second == {"items": [1, 2]}


def test_edit_state_commits_mutations_and_rolls_back_exceptions(monkeypatch, tmp_path):
    values = install_fake_database(monkeypatch)
    path = tmp_path / "state.json"

    with shared_state_store.edit_state(path, []) as items:
        items.append({"event": "committed"})
    assert shared_state_store.read_state(path, []) == [{"event": "committed"}]

    with pytest.raises(RuntimeError, match="abort"):
        with shared_state_store.edit_state(path, []) as items:
            items.append({"event": "must-rollback"})
            raise RuntimeError("abort")

    assert shared_state_store.read_state(path, []) == [{"event": "committed"}]
    assert len(values) == 1


def test_user_scope_override_is_supported_without_token(monkeypatch):
    monkeypatch.delenv("NOUS_TOKEN", raising=False)
    monkeypatch.setenv("NOUS_MEMORY_USER_ID", "explicit-owner")
    assert shared_state_store.user_id() == "explicit-owner"
