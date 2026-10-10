import hashlib
import json
import zipfile

from executor.brain_restore import inspect_brain_backup, restore_brain_backup


def _make_backup(path, entries):
    manifest = {"type": "NOUS_BRAIN_BACKUP", "version": 2, "files": []}
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            if isinstance(data, str):
                data = data.encode()
            archive.writestr(name, data)
            manifest["files"].append({
                "path": name,
                "sha256": hashlib.sha256(data).hexdigest(),
                "size": len(data),
            })
        archive.writestr("manifest.json", json.dumps(manifest))
    return path


def test_rejects_path_traversal(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    backup = _make_backup(tmp_path / "bad.zip", {"data/../../outside.json": b'{"pwned": true}'})
    result = inspect_brain_backup(str(backup))
    assert not result["ok"]
    assert any(p["error"] == "path_not_allowed" for p in result["problems"])
    assert restore_brain_backup(str(backup), apply=True)["ok"] is False
    assert not (tmp_path / "outside.json").exists()


def test_rejects_api_tokens_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    backup = _make_backup(tmp_path / "tokens.zip", {"data/api_tokens.json": b'[]'})
    result = inspect_brain_backup(str(backup))
    assert not result["ok"]
    assert any(p["error"] == "path_not_allowed" for p in result["problems"])


def test_restores_valid_json_inside_data(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "data" / "memory.json"
    target.parent.mkdir()
    target.write_text('{"old": true}', encoding="utf-8")
    backup = _make_backup(tmp_path / "good.zip", {"data/memory.json": b'{"new": true}'})
    result = restore_brain_backup(str(backup), apply=True)
    assert result["ok"]
    assert target.read_text(encoding="utf-8") == '{"new": true}'
    assert (tmp_path / result["safety_backup"] / "data" / "memory.json").exists()


def test_restores_binary_upload_and_generated_app(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    upload = b"%PDF-1.7\x00binary content"
    html = b"<h1>restored app</h1>"
    backup = _make_backup(tmp_path / "assets.zip", {
        "data/document_uploads/scan.pdf": upload,
        "data/generated_apps/demo/index.html": html,
    })
    result = restore_brain_backup(str(backup), apply=True)
    assert result["ok"]
    assert (tmp_path / "data/document_uploads/scan.pdf").read_bytes() == upload
    assert (tmp_path / "data/generated_apps/demo/index.html").read_bytes() == html


def test_rejects_non_json_runtime_files_outside_data(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    backup = _make_backup(tmp_path / "outside.zip", {"executor/module.py": b"print('no')"})
    assert inspect_brain_backup(str(backup))["ok"] is False


def test_rejects_unlisted_zip_entries(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    backup = tmp_path / "extra.zip"
    with zipfile.ZipFile(backup, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("data/memory.json", '{"ok":true}')
        archive.writestr("manifest.json", json.dumps({
            "type": "NOUS_BRAIN_BACKUP", "version": 2, "files": []
        }))
    result = inspect_brain_backup(str(backup))
    assert not result["ok"]
    assert any(p["error"] == "unlisted_zip_entries" for p in result["problems"])
