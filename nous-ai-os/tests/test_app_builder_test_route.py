from executor import app_builder, app_validation_runner, router


def test_app_test_endpoint_requires_admin_token(monkeypatch):
    monkeypatch.setattr(router, "check_admin_token", lambda _request: False)
    client = router.app.test_client()

    response = client.post(
        "/remote/app-builder/test",
        json={"app_name": "sample_app"},
    )

    assert response.status_code == 401
    assert response.get_json()["error"] == "unauthorized"


def test_app_test_endpoint_rejects_non_object_json(monkeypatch):
    monkeypatch.setattr(router, "check_admin_token", lambda _request: True)
    client = router.app.test_client()

    response = client.post(
        "/remote/app-builder/test",
        data='["sample_app"]',
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "invalid_request_body"


def test_app_test_endpoint_returns_real_runner_result(monkeypatch, tmp_path):
    monkeypatch.setattr(router, "check_admin_token", lambda _request: True)
    monkeypatch.setattr(app_builder, "APPS_DIR", tmp_path / "generated")
    calls = []

    def fake_runner(app_name, apps_root, timeout_seconds):
        calls.append((app_name, apps_root, timeout_seconds))
        return {
            "ok": True,
            "status": "passed",
            "return_code": 0,
            "isolation": {"security_sandbox": False},
        }

    monkeypatch.setattr(app_validation_runner, "run_project_tests", fake_runner)
    client = router.app.test_client()

    response = client.post(
        "/remote/app-builder/test",
        json={"app_name": "sample_app", "timeout_seconds": 30},
    )

    assert response.status_code == 200
    assert response.get_json()["status"] == "passed"
    assert calls == [("sample_app", tmp_path / "generated", 30)]


def test_app_test_endpoint_maps_failed_tests_to_unprocessable(monkeypatch, tmp_path):
    monkeypatch.setattr(router, "check_admin_token", lambda _request: True)
    monkeypatch.setattr(app_builder, "APPS_DIR", tmp_path / "generated")
    monkeypatch.setattr(
        app_validation_runner,
        "run_project_tests",
        lambda *_args: {"ok": False, "status": "failed", "return_code": 1},
    )

    response = router.app.test_client().post(
        "/remote/app-builder/test",
        json={"app_name": "sample_app"},
    )

    assert response.status_code == 422
    assert response.get_json()["status"] == "failed"
