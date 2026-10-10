import json
import zipfile

from executor import cloud_brain_backup


def test_backup_includes_runtime_json_but_excludes_tokens_and_archives(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data = tmp_path / "data"
    data.mkdir()
    (data / "memory.json").write_text('{"m": 1}', encoding="utf-8")
    (data / "conversation_history.json").write_text('{"c": 2}', encoding="utf-8")
    (data / "api_tokens.json").write_text('[{"token_hash":"never-backup"}]', encoding="utf-8")
    (data / "brain_backups").mkdir()
    (data / "brain_backups" / "old.zip").write_bytes(b"not a backup")
    monkeypatch.setattr(cloud_brain_backup, "BACKUP_DIR", "data/brain_backups")
    monkeypatch.setattr(cloud_brain_backup, "save_brain_state", lambda: None)

    result = cloud_brain_backup.create_brain_backup()
    assert result["ok"]
    with zipfile.ZipFile(result["backup"]) as archive:
        names = set(archive.namelist())
        manifest = json.loads(archive.read("manifest.json"))
    assert "data/memory.json" in names
    assert "data/conversation_history.json" in names
    assert "data/api_tokens.json" not in names
    assert "data/brain_backups/old.zip" not in names
    assert "data/conversation_history.json" in {item["path"] for item in manifest["files"]}
