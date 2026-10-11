import json
import shlex
import sys

from executor import app_builder, router


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



def test_generated_web_app_is_created_under_persistent_data_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(app_builder, "APP_DIR", "data/generated_apps")
    result = app_builder.make_web_app("persistent_demo", title="Persistent Demo")
    expected = tmp_path / "data" / "generated_apps" / "persistent_demo" / "index.html"
    assert result["created"] is True
    assert expected.is_file()
    assert result["url"] == "/apps/persistent_demo/"


def test_approved_app_run_command_points_to_written_entrypoint(tmp_path, monkeypatch):
    _queue_plan(tmp_path, monkeypatch, [
        {"path": "demo_app/main.py", "content": "print('safe')"},
    ])
    result = app_builder.approve_and_write("plan-1")
    assert result["ok"] is True
    assert result["run_command"].endswith("demo_app/main.py")



def test_autorepair_does_not_follow_symlink_outside_app(tmp_path):
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    outside = tmp_path / "outside.py"
    original = '{"files": [{"content": "def repaired():\\n    return True"}]}'
    outside.write_text(original, encoding="utf-8")
    (app_dir / "main.py").symlink_to(outside)

    result = router._try_autorepair_app(app_dir)

    assert result["repaired"] is False
    assert outside.read_text(encoding="utf-8") == original


def test_app_run_command_preserves_paths_with_spaces(tmp_path):
    app_dir = tmp_path / "generated app"
    app_dir.mkdir()
    script = app_dir / "main.py"
    script.write_text("print('ok')", encoding="utf-8")

    command = router._detect_run_command(app_dir)

    assert shlex.split(command) == [sys.executable, str(script.resolve())]


def test_app_launch_rejects_entrypoint_outside_app_directory(tmp_path):
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    outside = tmp_path / "outside.py"
    outside.write_text("print('outside')", encoding="utf-8")
    command = shlex.join([sys.executable, str(outside)])

    try:
        router._launch_app_proc(command, "sample", app_dir)
    except ValueError as exc:
        assert str(exc) == "app_entrypoint_outside_app_directory"
    else:
        raise AssertionError("expected app entrypoint path rejection")
