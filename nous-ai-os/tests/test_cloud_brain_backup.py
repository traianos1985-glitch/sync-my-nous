import json
import zipfile

from executor import cloud_brain_backup


def test_backup_includes_runtime_files_and_excludes_secrets_and_archives(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data = tmp_path / "data"
    data.mkdir()
    (data / "memory.json").write_text('{"m": 1}', encoding="utf-8")
    (data / "conversation_history.json").write_text('{"c": 2}', encoding="utf-8")
    (data / "api_tokens.json").write_text('[{"token_hash":"never-backup"}]', encoding="utf-8")
    (data / "secrets.json").write_text('{"secret":"never-backup"}', encoding="utf-8")
    uploads = data / "document_uploads"
    uploads.mkdir()
    (uploads / "scan.pdf").write_bytes(b"%PDF-1.7\x00binary")
    apps = data / "generated_apps" / "demo"
    apps.mkdir(parents=True)
    (apps / "index.html").write_text("<h1>demo</h1>", encoding="utf-8")
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
    assert "data/document_uploads/scan.pdf" in names
    assert "data/generated_apps/demo/index.html" in names
    assert "data/api_tokens.json" not in names
    assert "data/secrets.json" not in names
    assert "data/brain_backups/old.zip" not in names
    assert "data/conversation_history.json" in {item["path"] for item in manifest["files"]}
    assert manifest["version"] == 2
