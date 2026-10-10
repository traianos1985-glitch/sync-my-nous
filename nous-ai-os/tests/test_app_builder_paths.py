import json

from executor import app_builder


def _queue_plan(tmp_path, monkeypatch, file_specs):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(app_builder, "QUEUE", tmp_path / "data" / "app_builder_queue.json")
    monkeypatch.setattr(app_builder, "APPS_DIR", tmp_path / "apps")
    app_builder.QUEUE.parent.mkdir(parents=True, exist_ok=True)
    app_builder.QUEUE.write_text(json.dumps([{
        "plan_id": "plan-1",
        "status": "pending_approval",
        "app_name": "demo_app",
        "files": file_specs,
    }]), encoding="utf-8")


def test_rejects_traversal_without_writing_any_file(tmp_path, monkeypatch):
    _queue_plan(tmp_path, monkeypatch, [
        {"path": "demo_app/main.py", "content": "print('safe')"},
        {"path": "../../outside.py", "content": "print('unsafe')"},
    ])
    result = app_builder.approve_and_write("plan-1")
    assert result["ok"] is False
    assert result["error"] == "unsafe_app_path"
    assert not (tmp_path / "apps" / "demo_app" / "main.py").exists()
    assert not (tmp_path / "outside.py").exists()


def test_accepts_paths_inside_named_app_directory(tmp_path, monkeypatch):
    _queue_plan(tmp_path, monkeypatch, [
        {"path": "demo_app/main.py", "content": "print('safe')"},
    ])
    result = app_builder.approve_and_write("plan-1")
    assert result["ok"] is True
    assert (tmp_path / "apps" / "demo_app" / "main.py").read_text(encoding="utf-8") == "print('safe')"


def test_rejects_absolute_and_windows_paths(tmp_path, monkeypatch):
    for unsafe in ("/tmp/pwn.py", "C:/tmp/pwn.py", "demo_app\\..\\outside.py"):
        _queue_plan(tmp_path, monkeypatch, [{"path": unsafe, "content": "bad"}])
        result = app_builder.approve_and_write("plan-1")
        assert result["ok"] is False
        assert result["error"] == "unsafe_app_path"
