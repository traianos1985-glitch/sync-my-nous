from executor import app_builder, app_failure_diagnosis, app_repair_review, app_validation_runner, router


def test_diagnosis_endpoint_requires_admin(monkeypatch):
    monkeypatch.setattr(router, "check_admin_token", lambda _request: False)
    response = router.app.test_client().post(
        "/remote/app-builder/diagnose", json={"app_name": "sample_app"}
    )
    assert response.status_code == 401
    assert response.get_json()["error"] == "unauthorized"


def test_diagnosis_endpoint_rejects_invalid_body(monkeypatch):
    monkeypatch.setattr(router, "check_admin_token", lambda _request: True)
    response = router.app.test_client().post(
        "/remote/app-builder/diagnose", data="[]", content_type="application/json"
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "invalid_request_body"


def test_diagnosis_endpoint_does_not_call_llm_when_tests_pass(monkeypatch, tmp_path):
    monkeypatch.setattr(router, "check_admin_token", lambda _request: True)
    monkeypatch.setattr(app_builder, "APPS_DIR", tmp_path / "apps")
    monkeypatch.setattr(
        app_validation_runner, "run_project_tests",
        lambda *_args: {"ok": True, "status": "passed", "return_code": 0},
    )
    monkeypatch.setattr(
        app_failure_diagnosis, "diagnose_test_failure",
        lambda *_args: (_ for _ in ()).throw(AssertionError("must not diagnose passing tests")),
    )
    response = router.app.test_client().post(
        "/remote/app-builder/diagnose", json={"app_name": "sample_app"}
    )
    assert response.status_code == 200
    assert response.get_json()["status"] == "tests_passed"
    assert response.get_json()["diagnosis"] is None


def test_diagnosis_endpoint_returns_review_only_proposal(monkeypatch, tmp_path):
    monkeypatch.setattr(router, "check_admin_token", lambda _request: True)
    apps_root = tmp_path / "apps"
    (apps_root / "sample_app").mkdir(parents=True)
    monkeypatch.setattr(app_builder, "APPS_DIR", apps_root)
    monkeypatch.setattr(
        app_validation_runner, "run_project_tests",
        lambda *_args: {
            "ok": False, "status": "failed", "return_code": 1,
            "stdout": "assert 1 == 2", "stderr": "",
        },
    )
    monkeypatch.setattr(
        app_repair_review, "save_repair_proposal",
        lambda *_args: {"ok": True, "repair_id": "repair_" + "a" * 32},
    )
    monkeypatch.setattr(
        app_failure_diagnosis, "diagnose_test_failure",
        lambda *_args: {
            "ok": True, "status": "proposal_ready", "writes_performed": False,
            "human_review_required": True, "changes": [],
        },
    )
    response = router.app.test_client().post(
        "/remote/app-builder/diagnose",
        json={"app_name": "sample_app", "timeout_seconds": 30},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "diagnosis_ready"
    assert payload["test_result"]["status"] == "failed"
    assert payload["diagnosis"]["writes_performed"] is False
    assert payload["human_review_required"] is True
    assert payload["repair_id"] == "repair_" + "a" * 32


def test_repair_review_endpoint_requires_admin(monkeypatch):
    monkeypatch.setattr(router, "check_admin_token", lambda _request: False)
    response = router.app.test_client().post(
        "/remote/app-builder/repair-review", json={"repair_id": "repair_" + "a" * 32}
    )
    assert response.status_code == 401


def test_repair_review_endpoint_returns_static_report(monkeypatch, tmp_path):
    monkeypatch.setattr(router, "check_admin_token", lambda _request: True)
    monkeypatch.setattr(app_builder, "APPS_DIR", tmp_path / "apps")
    monkeypatch.setattr(
        app_repair_review, "review_repair_proposal",
        lambda *_args: {
            "ok": True, "status": "blocked", "ready_for_human_review": False,
            "writes_performed": False, "tests_executed": False,
        },
    )
    response = router.app.test_client().post(
        "/remote/app-builder/repair-review",
        json={"repair_id": "repair_" + "a" * 32},
    )
    assert response.status_code == 200
    assert response.get_json()["writes_performed"] is False


def test_repair_review_endpoint_rejects_invalid_body(monkeypatch):
    monkeypatch.setattr(router, "check_admin_token", lambda _request: True)
    response = router.app.test_client().post(
        "/remote/app-builder/repair-review", data="[]", content_type="application/json"
    )
    assert response.status_code == 400


def test_diagnosis_endpoint_maps_runner_errors_without_llm(monkeypatch, tmp_path):
    monkeypatch.setattr(router, "check_admin_token", lambda _request: True)
    monkeypatch.setattr(app_builder, "APPS_DIR", tmp_path / "apps")
    monkeypatch.setattr(
        app_validation_runner, "run_project_tests",
        lambda *_args: {"ok": False, "error": "automated_tests_not_found"},
    )
    response = router.app.test_client().post(
        "/remote/app-builder/diagnose", json={"app_name": "sample_app"}
    )
    assert response.status_code == 404
    assert response.get_json()["status"] == "test_run_unavailable"
