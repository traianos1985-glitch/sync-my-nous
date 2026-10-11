"""Regression tests for the operational API's admin boundary and self-heal command sink."""

import pytest

pytest.importorskip("flask")


def test_self_heal_rejects_non_admin_before_processing_payload(monkeypatch):
    from executor import router
    from executor.blueprints import agent_ops_bp

    token = "self-heal-user-token-boundary"
    monkeypatch.setenv("NOUS_TOKEN", token)
    monkeypatch.setattr(agent_ops_bp, "check_admin_token", lambda _request: False)

    def must_not_run(*_args, **_kwargs):
        pytest.fail("self-heal must not run for a non-admin token")

    monkeypatch.setattr(agent_ops_bp, "self_heal_snippet", must_not_run)
    response = router.app.test_client().post(
        "/api/ops/self-heal/run",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "filename": "scratch.py",
            "code": "x = 1",
            "test_cmd": "python3 -c \"import os; print(os.environ['NOUS_TOKEN'])\"",
        },
    )

    assert response.status_code == 401
    assert response.get_json()["error"] == "unauthorized"


def test_self_heal_never_forwards_caller_command(monkeypatch):
    from executor import router
    from executor.blueprints import agent_ops_bp

    token = "self-heal-admin-token-boundary"
    monkeypatch.setenv("NOUS_TOKEN", token)
    monkeypatch.setattr(agent_ops_bp, "check_admin_token", lambda _request: True)
    captured = {}

    def fake_self_heal(filename, code):
        captured["filename"] = filename
        captured["code"] = code
        return {"success": True}

    monkeypatch.setattr(agent_ops_bp, "self_heal_snippet", fake_self_heal)
    response = router.app.test_client().post(
        "/api/ops/self-heal/run",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "filename": "scratch.py",
            "code": "x = 1",
            "test_cmd": "python3 -c \"import os; print(os.environ['NOUS_TOKEN'])\"",
        },
    )

    assert response.status_code == 200
    assert captured == {"filename": "scratch.py", "code": "x = 1"}
