import hashlib
import importlib
import json
import sqlite3
import zipfile
from pathlib import Path

import pytest


def test_sqlite_memory_returns_newest_records_in_chronological_order(tmp_path, monkeypatch):
    from executor import sqlite_store

    monkeypatch.chdir(tmp_path)
    store = importlib.reload(sqlite_store)
    monkeypatch.setattr(store, "DB_PATH", "data/memory.db")
    store.init_db()
    for index in range(1, 7):
        store.save_memory({"number": index})

    assert store.load_memories(3) == [{"number": 4}, {"number": 5}, {"number": 6}]
    assert store.inspect_sqlite_store()["ok"] is True


@pytest.mark.parametrize("limit", [0, -1, True, 1.5, "2", None])
def test_sqlite_memory_rejects_invalid_limits(tmp_path, monkeypatch, limit):
    from executor import sqlite_store

    monkeypatch.chdir(tmp_path)
    store = importlib.reload(sqlite_store)
    monkeypatch.setattr(store, "DB_PATH", "data/memory.db")
    with pytest.raises(ValueError, match="memory_limit_must_be_positive_integer"):
        store.load_memories(limit)


def test_sqlite_memory_fails_closed_on_corrupt_record(tmp_path, monkeypatch):
    from executor import sqlite_store

    monkeypatch.chdir(tmp_path)
    store = importlib.reload(sqlite_store)
    monkeypatch.setattr(store, "DB_PATH", "data/memory.db")
    store.init_db()
    conn = sqlite3.connect(store.DB_PATH)
    try:
        conn.execute("INSERT INTO memories(timestamp, data) VALUES (?, ?)", (1.0, "{bad"))
        conn.commit()
    finally:
        conn.close()

    with pytest.raises(RuntimeError, match="memory_store_integrity_failure"):
        store.load_memories()
    health = store.inspect_sqlite_store()
    assert health["ok"] is False
    assert health["malformed_records"] == 1


def _make_backup(path: Path, members: dict[str, bytes]):
    manifest = {
        "type": "NOUS_BRAIN_BACKUP",
        "version": 2,
        "created": 1.0,
        "files": [
            {"path": name, "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
            for name, data in members.items()
        ],
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in members.items():
            archive.writestr(name, data)
        archive.writestr("manifest.json", json.dumps(manifest))


def test_restore_preview_then_apply_and_preserve_safety_copy(tmp_path, monkeypatch):
    from executor import brain_restore

    monkeypatch.chdir(tmp_path)
    module = importlib.reload(brain_restore)
    monkeypatch.setattr(module, "RESTORE_DIR", "data/brain_restores")
    target = Path("data/settings.json")
    target.parent.mkdir(parents=True)
    target.write_text('{"old": true}', encoding="utf-8")
    backup = tmp_path / "valid.zip"
    payload = b'{"new": true}'
    _make_backup(backup, {"data/settings.json": payload})

    preview = module.restore_brain_backup(str(backup))
    assert preview["ok"] is True and preview["preview"] is True
    assert json.loads(target.read_text(encoding="utf-8")) == {"old": True}

    applied = module.restore_brain_backup(str(backup), apply=True)
    assert applied["ok"] is True
    assert json.loads(target.read_text(encoding="utf-8")) == {"new": True}
    saved = Path(applied["safety_backup"]) / "data/settings.json"
    assert json.loads(saved.read_text(encoding="utf-8")) == {"old": True}


def test_restore_rejects_bad_hash_before_touching_live_files(tmp_path, monkeypatch):
    from executor import brain_restore

    monkeypatch.chdir(tmp_path)
    module = importlib.reload(brain_restore)
    target = Path("data/settings.json")
    target.parent.mkdir(parents=True)
    target.write_text('{"original": 1}', encoding="utf-8")
    backup = tmp_path / "bad.zip"
    with zipfile.ZipFile(backup, "w") as archive:
        archive.writestr("data/settings.json", '{"tampered": 2}')
        archive.writestr("manifest.json", json.dumps({
            "type": "NOUS_BRAIN_BACKUP",
            "version": 2,
            "files": [{"path": "data/settings.json", "sha256": "0" * 64, "size": 14}],
        }))

    result = module.restore_brain_backup(str(backup), apply=True)
    assert result["ok"] is False
    assert result["error"] == "inspection_failed"
    assert target.read_text(encoding="utf-8") == '{"original": 1}'


def test_restore_rejects_symlink_target_before_any_write(tmp_path, monkeypatch):
    from executor import brain_restore

    monkeypatch.chdir(tmp_path)
    module = importlib.reload(brain_restore)
    data = Path("data")
    data.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text('{"untouched": true}', encoding="utf-8")
    (data / "redirect.json").symlink_to(outside)
    backup = tmp_path / "symlink.zip"
    _make_backup(backup, {
        "data/ordinary.json": b'{"should_not": "apply"}',
        "data/redirect.json": b'{"unsafe": true}',
    })

    result = module.restore_brain_backup(str(backup), apply=True)
    assert result["ok"] is False
    assert not (data / "ordinary.json").exists()
    assert outside.read_text(encoding="utf-8") == '{"untouched": true}'


def test_backup_is_published_as_verified_zip(tmp_path, monkeypatch):
    from executor import cloud_brain_backup as backup_module
    from executor import brain_restore

    monkeypatch.chdir(tmp_path)
    module = importlib.reload(backup_module)
    monkeypatch.setattr(module, "BACKUP_DIR", "data/brain_backups")
    monkeypatch.setattr(module, "DATA_ROOT", Path("data"))
    monkeypatch.setattr(module, "save_brain_state", lambda: None)
    data = Path("data")
    data.mkdir()
    (data / "state.json").write_text('{"ready": true}', encoding="utf-8")
    (data / "api_tokens.json").write_text('{"secret": "never-backup"}', encoding="utf-8")
    private = data / "private"
    private.mkdir()
    (private / "credentials.json").write_text('{"secret": "nested-never-backup"}', encoding="utf-8")

    result = module.create_brain_backup()
    assert result["ok"] is True
    assert zipfile.is_zipfile(result["backup"])
    assert result["sha256"]
    assert not list(Path("data/brain_backups").glob("*.tmp"))
    inspection = brain_restore.inspect_brain_backup(result["backup"])
    assert inspection["ok"] is True
    assert [item["path"] for item in inspection["files"]] == ["data/state.json"]


def test_restore_rejects_nested_secret_filename_before_any_write(tmp_path, monkeypatch):
    from executor import brain_restore

    monkeypatch.chdir(tmp_path)
    module = importlib.reload(brain_restore)
    data = Path("data")
    data.mkdir()
    target = data / "ordinary.json"
    backup = tmp_path / "nested-secret.zip"
    _make_backup(backup, {
        "data/ordinary.json": b'{"should_not": "apply"}',
        "data/private/api_tokens.json": b'{"secret": true}',
    })

    result = module.restore_brain_backup(str(backup), apply=True)
    assert result["ok"] is False
    assert not target.exists()
    assert any(problem["error"] == "path_not_allowed" for problem in result["inspection"]["problems"])



def test_sqlite_store_diagnostics_report_malformed_records(tmp_path, monkeypatch):
    from executor import sqlite_store

    monkeypatch.chdir(tmp_path)
    store = importlib.reload(sqlite_store)
    monkeypatch.setattr(store, "DB_PATH", "data/memory.db")
    store.init_db()
    store.save_memory({"healthy": True})
    health = store.inspect_sqlite_store()
    assert health["ok"] is True
    assert health["record_count"] == 1
    assert health["malformed_records"] == 0

    conn = sqlite3.connect(store.DB_PATH)
    try:
        conn.execute("INSERT INTO memories(timestamp, data) VALUES (?, ?)", (2.0, "{bad"))
        conn.commit()
    finally:
        conn.close()
    health = store.inspect_sqlite_store()
    assert health["ok"] is False
    assert health["malformed_records"] == 1
