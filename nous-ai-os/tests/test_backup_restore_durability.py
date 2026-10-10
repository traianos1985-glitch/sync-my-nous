import json
import os
import zipfile
from pathlib import Path

from executor import brain_restore, cloud_brain_backup


def test_backup_is_verified_and_published_without_temporary_archives(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data = Path("data")
    data.mkdir()
    (data / "memory.json").write_text('[{"note":"persist"}]', encoding="utf-8")
    monkeypatch.setattr(cloud_brain_backup, "BACKUP_DIR", "data/brain_backups")
    monkeypatch.setattr(cloud_brain_backup, "save_brain_state", lambda: None)

    result = cloud_brain_backup.create_brain_backup()

    assert result["ok"] is True
    assert result["verified"] is True
    assert len(result["sha256"]) == 64
    assert zipfile.is_zipfile(result["backup"])
    assert [name for name in os.listdir("data/brain_backups") if name.endswith(".tmp")] == []
    with zipfile.ZipFile(result["backup"]) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["type"] == "NOUS_BRAIN_BACKUP"
        assert "data/memory.json" in {item["path"] for item in manifest["files"]}


def test_restore_rejects_symlinked_target_and_leaves_outside_file_untouched(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data = Path("data")
    data.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text('{"outside":true}', encoding="utf-8")
    (data / "linked.json").symlink_to(outside)
    backup = tmp_path / "linked.zip"

    import hashlib
    with zipfile.ZipFile(backup, "w", zipfile.ZIP_DEFLATED) as archive:
        payload = b'{"changed":true}'
        archive.writestr("data/linked.json", payload)
        archive.writestr("manifest.json", json.dumps({
            "type": "NOUS_BRAIN_BACKUP", "version": 2,
            "files": [{"path": "data/linked.json",
                       "sha256": hashlib.sha256(payload).hexdigest(),
                       "size": len(payload)}],
        }))

    result = brain_restore.restore_brain_backup(str(backup), apply=True)
    assert result["ok"] is False
    assert outside.read_text(encoding="utf-8") == '{"outside":true}'


def test_restore_rolls_back_already_replaced_files_if_later_replace_fails(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data = Path("data")
    data.mkdir()
    first = data / "first.json"
    second = data / "second.json"
    first.write_text('{"old":1}', encoding="utf-8")
    second.write_text('{"old":2}', encoding="utf-8")

    import hashlib
    backup = tmp_path / "multi.zip"
    entries = {"data/first.json": b'{"new":1}', "data/second.json": b'{"new":2}'}
    with zipfile.ZipFile(backup, "w", zipfile.ZIP_DEFLATED) as archive:
        manifest_files = []
        for name, payload in entries.items():
            archive.writestr(name, payload)
            manifest_files.append({"path": name, "sha256": hashlib.sha256(payload).hexdigest(), "size": len(payload)})
        archive.writestr("manifest.json", json.dumps({
            "type": "NOUS_BRAIN_BACKUP", "version": 2, "files": manifest_files,
        }))

    original_replace = os.replace
    failed = {"done": False}

    def fail_second_once(source, destination):
        if str(destination).endswith("second.json") and not failed["done"]:
            failed["done"] = True
            raise OSError("simulated disk failure")
        return original_replace(source, destination)

    monkeypatch.setattr(brain_restore.os, "replace", fail_second_once)
    result = brain_restore.restore_brain_backup(str(backup), apply=True)

    assert result["ok"] is False
    assert result["rolled_back"] is True
    assert json.loads(first.read_text(encoding="utf-8")) == {"old": 1}
    assert json.loads(second.read_text(encoding="utf-8")) == {"old": 2}
