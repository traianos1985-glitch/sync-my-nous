import pytest
from flask import Flask

from executor.blueprints import agent_environments_bp as environments


@pytest.fixture
def client(monkeypatch):
    app = Flask(__name__)
    app.register_blueprint(environments.agent_environments_bp)
    monkeypatch.setattr(environments, "check_admin_token", lambda _request: True)
    return app.test_client()


@pytest.mark.parametrize("payload", [
    [],
    ["provider", "render"],
    "render",
    7,
    None,
])
def test_probe_rejects_non_object_json_without_running_provider(monkeypatch, client, payload):
    monkeypatch.setattr(
        environments, "probe_provider",
        lambda _provider: pytest.fail("provider probe must not run for invalid JSON shape"),
    )
    response = client.post("/api/agent-environments/probe", json=payload)
    assert response.status_code == 400
    assert response.get_json() == {"ok": False, "error": "json_object_required"}


@pytest.mark.parametrize("payload", [
    [],
    "DEPLOY",
    1,
    None,
])
def test_deploy_rejects_non_object_json_after_authentication(monkeypatch, client, payload):
    monkeypatch.setattr(
        environments, "deploy_provider",
        lambda **_kwargs: pytest.fail("deployment must not run for invalid JSON shape"),
    )
    response = client.post("/api/agent-environments/deploy", json=payload)
    assert response.status_code == 400
    assert response.get_json() == {"ok": False, "error": "json_object_required"}


@pytest.mark.parametrize("payload", [
    [],
    "project",
    1,
    None,
])
def test_preflight_rejects_non_object_json_without_inspection(monkeypatch, client, payload):
    monkeypatch.setattr(
        environments, "inspect_preview_compatibility",
        lambda *_args: pytest.fail("preflight must not run for invalid JSON shape"),
    )
    response = client.post("/api/agent-environments/preflight", json=payload)
    assert response.status_code == 400
    assert response.get_json() == {"ok": False, "error": "json_object_required"}


def test_probe_accepts_object_json(monkeypatch, client):
    monkeypatch.setattr(
        environments, "probe_provider",
        lambda provider: {"ok": True, "provider": provider},
    )
    response = client.post("/api/agent-environments/probe", json={"provider": "render"})
    assert response.status_code == 200
    assert response.get_json() == {"ok": True, "provider": "render"}
