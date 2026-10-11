"""Regression coverage for ReAct workspace containment, self-improvement safety, and auth lockout."""
import json
from pathlib import Path


def test_react_file_tools_confine_io_to_workspace(monkeypatch, tmp_path):
    from executor import react_agent

    monkeypatch.setattr(react_agent, "WORKSPACE", tmp_path / "workspace")
    registry = react_agent.ToolRegistry()
    write_file = registry.get("write_file")
    read_file = registry.get("read_file")
    list_dir = registry.get("list_dir")

    assert write_file("notes/hello.txt", "hello").startswith("[SUCCESS]")
    assert read_file("notes/hello.txt") == "hello"
    assert "hello.txt" in json.loads(list_dir("notes"))
    assert "path_outside_workspace" in write_file("../../outside.txt", "bad")
    assert "path_outside_workspace" in read_file("/etc/passwd")
    assert not (tmp_path / "outside.txt").exists()


def test_react_file_tools_reject_symlink_escape(monkeypatch, tmp_path):
    from executor import react_agent

    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside"
    workspace.mkdir()
    outside.mkdir()
    (workspace / "escape").symlink_to(outside, target_is_directory=True)
    monkeypatch.setattr(react_agent, "WORKSPACE", workspace)
    registry = react_agent.ToolRegistry()

    result = registry.get("write_file")("escape/pwned.txt", "bad")
    assert "path_outside_workspace" in result
    assert not (outside / "pwned.txt").exists()


def test_self_improvement_rejects_traversal_patch_ids(monkeypatch, tmp_path):
    from executor import self_improvement_engine as engine

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(engine, "check_action", lambda _action: {"allowed": False})
    assert engine.apply_patch("../../outside") == {"ok": False, "error": "invalid_patch_id"}


def test_self_improvement_cannot_patch_security_policy(monkeypatch, tmp_path):
    from executor import self_improvement_engine as engine

    monkeypatch.chdir(tmp_path)
    result = engine.create_patch_request("executor/guardian_policy.py", "BLOCKED_ACTIONS = set()")
    assert result["created"] is False
    assert result["error"] == "file_not_allowed"


def test_self_improvement_compile_failure_preserves_live_file(monkeypatch, tmp_path):
    from executor import self_improvement_engine as engine

    monkeypatch.chdir(tmp_path)
    (tmp_path / "executor").mkdir()
    target = tmp_path / "executor" / "learning_engine.py"
    target.write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "data" / "patches").mkdir(parents=True)
    patch_id = "123456789"
    (tmp_path / "data" / "patches" / f"{patch_id}.json").write_text(
        json.dumps({"id": int(patch_id), "file": "executor/learning_engine.py",
                    "new_content": "def broken(:\n", "status": "pending"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(engine, "check_action", lambda _action: {"allowed": False})

    result = engine.apply_patch(patch_id)
    assert result["ok"] is False
    assert result["rolled_back"] is True
    assert target.read_text(encoding="utf-8") == "VALUE = 1\n"


def test_auth_lockout_does_not_block_valid_credentials(monkeypatch):
    from flask import Flask
    from executor import auth_guard

    client_ip = "192.0.2.234"
    auth_guard._clear_auth_failures(client_ip)
    for _ in range(auth_guard.AUTH_FAILURE_LIMIT):
        auth_guard._record_auth_failure(client_ip)

    monkeypatch.setattr(auth_guard, "check_token", lambda _request: True)
    app = Flask(__name__)
    auth_guard.install_auth_guard(app)

    @app.get("/private")
    def private():
        return {"ok": True}

    response = app.test_client().get("/private", environ_base={"REMOTE_ADDR": client_ip})
    assert response.status_code == 200
    assert auth_guard._auth_state(client_ip) == (0, 0.0)


def test_procfile_uses_single_worker_for_in_process_schedulers():
    procfile = Path(__file__).resolve().parents[1] / "Procfile"
    content = procfile.read_text(encoding="utf-8")
    assert "--workers 1" in content
    assert "WEB_CONCURRENCY:-2" not in content
