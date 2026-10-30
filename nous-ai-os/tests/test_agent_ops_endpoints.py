"""HTTP contracts for the ReAct and bounded research operational endpoints."""
import pytest

pytest.importorskip("flask")


def test_react_endpoint_requires_admin_before_dispatch(monkeypatch):
    from flask import Flask
    from executor.blueprints import agent_ops_bp

    app = Flask(__name__)
    app.register_blueprint(agent_ops_bp.agent_ops_bp)
    monkeypatch.setattr(agent_ops_bp, "check_admin_token", lambda _request: False)
    monkeypatch.setattr(
        agent_ops_bp, "run_react_task",
        lambda *_args, **_kwargs: pytest.fail("ReAct must not run without admin scope"),
    )
    response = app.test_client().post(
        "/api/ops/react/run",
        headers={"Authorization": "Bearer test-user-token"},
        json={"task": "inspect status", "max_steps": 2},
    )
    assert response.status_code == 401
    assert response.get_json()["error"] == "unauthorized"


def test_react_endpoint_validates_payload_and_dispatches_bounded_request(monkeypatch):
    from flask import Flask
    from executor.blueprints import agent_ops_bp

    app = Flask(__name__)
    app.register_blueprint(agent_ops_bp.agent_ops_bp)
    monkeypatch.setattr(agent_ops_bp, "check_admin_token", lambda _request: True)
    calls = []
    monkeypatch.setattr(
        agent_ops_bp, "run_react_task",
        lambda task, max_steps: calls.append((task, max_steps)) or {"status": "completed"},
    )
    client = app.test_client()
    invalid = client.post("/api/ops/react/run", json={"task": "status", "max_steps": True})
    assert invalid.status_code == 400
    assert calls == []
    response = client.post("/api/ops/react/run", json={"task": "  inspect status  ", "max_steps": 3})
    assert response.status_code == 200
    assert response.get_json() == {"success": True, "result": {"status": "completed"}}
    assert calls == [("inspect status", 3)]


def test_url_reader_endpoint_requires_admin_and_uses_bounded_reader(monkeypatch):
    from flask import Flask
    from executor.blueprints import agent_ops_bp

    app = Flask(__name__)
    app.register_blueprint(agent_ops_bp.agent_ops_bp)
    monkeypatch.setattr(agent_ops_bp, "check_admin_token", lambda _request: False)
    monkeypatch.setattr(
        agent_ops_bp, "summarize_url",
        lambda *_args, **_kwargs: pytest.fail("URL reader must not run without admin scope"),
    )
    client = app.test_client()
    denied = client.post("/api/ops/research/read-url", json={"url": "https://example.com"})
    assert denied.status_code == 401

    monkeypatch.setattr(agent_ops_bp, "check_admin_token", lambda _request: True)
    calls = []
    monkeypatch.setattr(
        agent_ops_bp, "summarize_url",
        lambda url: calls.append(url) or {"ok": True, "mode": "url_reader", "title": "Example"},
    )
    invalid = client.post("/api/ops/research/read-url", json={"url": "x" * 2049})
    assert invalid.status_code == 400
    assert calls == []
    response = client.post("/api/ops/research/read-url", json={"url": " https://example.com "})
    assert response.status_code == 200
    assert response.get_json()["success"] is True
    assert calls == ["https://example.com"]
