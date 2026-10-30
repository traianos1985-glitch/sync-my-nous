import hashlib
import threading
from executor import app_builder, app_studio, app_validation_runner, router
from executor.app_repair_review import save_repair_proposal, resolve_repair_proposal


def proposal(tmp_path):
    root = tmp_path / "apps"
    app = root / "sample_app"
    app.mkdir(parents=True)
    target = app / "main.py"
    target.write_text("answer = 41\n")
    store = tmp_path / "repairs.json"
    diagnosis = {"ok": True, "app_name": "sample_app", "writes_performed": False,
                 "changes": [{"path": "sample_app/main.py", "content": "answer = 42\n"}],
                 "baseline_hashes": {"sample_app/main.py": hashlib.sha256(target.read_bytes()).hexdigest()}}
    saved = save_repair_proposal("sample_app", root, diagnosis, store)
    return root, target, store, saved["repair_id"]


def test_explicit_approval_applies_reviewed_patch_once(tmp_path):
    root, target, store, repair_id = proposal(tmp_path)
    result = resolve_repair_proposal(repair_id, root, approve=True, store_path=store)
    assert result["proposal_applied"] is True
    assert result["tests_executed"] is False
    assert target.read_text() == "answer = 42\n"


def test_launch_does_not_apply_unreviewed_repairs(monkeypatch, tmp_path):
    from types import SimpleNamespace
    app = tmp_path / "sample_app"
    app.mkdir()
    source = '{"files": []}\n'
    (app / "main.py").write_text(source)
    monkeypatch.setattr(router, "check_admin_token", lambda _: True)
    monkeypatch.setattr(router, "_find_builder_app_dir", lambda _: app)
    monkeypatch.setattr(router, "claim_approved_approval", lambda *_: True)
    monkeypatch.setattr(router, "finish_approval", lambda *_: None)
    monkeypatch.setattr(router, "_launch_app_proc", lambda *_: {"proc": SimpleNamespace(pid=1, poll=lambda: 1), "lines": ["SyntaxError\n"]})
    monkeypatch.setattr(router, "_try_autorepair_app", lambda *_: (_ for _ in ()).throw(AssertionError("unreviewed repair")))
    result = router.app.test_client().post("/remote/app-builder/run-app", json={"app": "sample_app", "approval_id": "approved"}).get_json()
    assert result["repaired"] is False
    assert result["running"] is False
    assert (app / "main.py").read_text() == source
    assert resolve_repair_proposal(repair_id, root, approve=True, store_path=store)["error"] == "repair_not_pending"


def test_rejection_never_writes_application_files(tmp_path):
    root, target, store, repair_id = proposal(tmp_path)
    result = resolve_repair_proposal(repair_id, root, approve=False, store_path=store)
    assert result["status"] == "rejected"
    assert target.read_text() == "answer = 41\n"


def test_approval_rechecks_changed_baseline(tmp_path):
    root, target, store, repair_id = proposal(tmp_path)
    target.write_text("answer = 99\n")
    result = resolve_repair_proposal(repair_id, root, approve=True, store_path=store)
    assert result["error"] == "repair_blocked"
    assert target.read_text() == "answer = 99\n"


def test_studio_routes_require_admin(monkeypatch):
    monkeypatch.setattr(app_studio, "check_admin_token", lambda _: False)
    client = router.app.test_client()
    for path in ("test-stream", "repair-approve", "repair-reject"):
        assert client.post("/remote/app-builder/" + path, json={}).status_code == 401
    assert client.get("/remote/app-builder/repairs?app=sample_app").status_code == 401


def test_live_runner_emits_actual_output_and_failure(tmp_path):
    root = tmp_path / "apps"
    tests = root / "sample_app" / "tests"
    tests.mkdir(parents=True)
    (tests / "test_main.py").write_text("def test_answer():\n    print('runner started', flush=True)\n    assert 41 == 42\n")
    output = []
    result = app_validation_runner.run_project_tests("sample_app", root, 15, on_output=output.append)
    assert result["status"] == "failed"
    assert result["return_code"] == 1
    assert "runner started" in "".join(output)
    assert "assert 41 == 42" in result["stdout"]


def test_live_runner_cancels_child(tmp_path):
    tests = tmp_path / "sample_app" / "tests"
    tests.mkdir(parents=True)
    (tests / "test_main.py").write_text("import time\ndef test_wait():\n    time.sleep(30)\n")
    cancelled = threading.Event()
    cancelled.set()
    result = app_validation_runner.run_project_tests("sample_app", tmp_path, 15, on_output=lambda _: None, cancelled=cancelled)
    assert result["status"] == "cancelled"
    assert result["ok"] is False


def test_stream_endpoint_delivers_terminal_result(monkeypatch):
    monkeypatch.setattr(app_studio, "check_admin_token", lambda _: True)
    def run(*args, on_output, cancelled):
        on_output("1 passed\n")
        return {"ok": True, "status": "passed"}
    monkeypatch.setattr(app_validation_runner, "run_project_tests", run)
    response = router.app.test_client().post("/remote/app-builder/test-stream", json={"app_name": "sample_app"})
    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'event: output' in text
    assert 'event: result' in text
    assert '"status": "passed"' in text


def test_repair_routes_preview_apply_and_reload(monkeypatch, tmp_path):
    root, target, store, repair_id = proposal(tmp_path)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "app_builder_repairs.json").write_text(store.read_text())
    monkeypatch.setattr(app_builder, "APPS_DIR", root)
    monkeypatch.setattr(app_studio, "check_admin_token", lambda _: True)
    client = router.app.test_client()
    detail = client.get("/remote/app-builder/repair/" + repair_id).get_json()
    assert "-answer = 41" in detail["changes"][0]["diff"]
    assert "+answer = 42" in detail["changes"][0]["diff"]
    assert target.read_text() == "answer = 41\n"
    assert client.post("/remote/app-builder/repair-approve", json={"repair_id": repair_id}).get_json()["proposal_applied"] is True
    assert client.get("/remote/app-builder/repairs?app=sample_app").get_json()["repairs"][0]["status"] == "applied"
    assert target.read_text() == "answer = 42\n"