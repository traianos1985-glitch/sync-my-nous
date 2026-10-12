import json
from types import SimpleNamespace

import pytest
from flask import Flask

from executor import fleet_agent, fleet_coordinator as fleet, fleet_rollout
from executor.blueprints.agent_environments_bp import agent_environments_bp


@pytest.fixture(autouse=True)
def isolated_registry(tmp_path, monkeypatch):
    monkeypatch.setenv("NOUS_FLEET_DB_PATH", str(tmp_path / "fleet-test.sqlite3"))
    monkeypatch.setenv("NOUS_FLEET_TARGET_VERSION", "release-2")
    monkeypatch.setenv("NOUS_VERSION", "release-2")
    fleet_agent.reset_heartbeat_for_tests()
    yield
    fleet.clear_fleet_registry_for_tests()


def test_heartbeat_records_metadata_and_reports_drift():
    result = fleet.record_heartbeat({
        "instance_id": "nous-vercel-01", "provider": "vercel",
        "version": "release-1", "commit_sha": "abcdef1234567", "status": "healthy",
    })
    assert result["ok"] is True
    assert result["update_available"] is True
    assert result["desired_version"] == "release-2"
    status = fleet.fleet_status()
    assert status["instance_count"] == 1
    assert status["outdated_count"] == 1
    assert status["instances"][0]["instance_id"] == "nous-vercel-01"


def test_same_heartbeat_updates_existing_instance_not_duplicate():
    payload = {"instance_id": "nous-render-01", "provider": "render", "version": "release-2"}
    assert fleet.record_heartbeat(payload)["ok"] is True
    assert fleet.record_heartbeat(payload)["ok"] is True
    assert fleet.fleet_status()["instance_count"] == 1


def test_rejects_invalid_metadata():
    assert fleet.record_heartbeat({"instance_id": "x", "provider": "vercel", "version": "v1"})["error"] == "invalid_instance_id"
    assert fleet.record_heartbeat({"instance_id": "nous-valid-01", "provider": "https://evil.example", "version": "v1"})["error"] == "invalid_provider"


def test_target_version_missing_disables_drift_claims(monkeypatch):
    monkeypatch.delenv("NOUS_FLEET_TARGET_VERSION")
    monkeypatch.delenv("NOUS_VERSION")
    result = fleet.record_heartbeat({"instance_id": "nous-unknown-01", "provider": "generic", "version": "v1"})
    assert result["ok"] is True
    assert result["update_available"] is False
    assert result["desired_version"] is None


def test_status_marks_stale_instances_without_deleting_them():
    fleet.record_heartbeat({"instance_id": "nous-codespaces-01", "provider": "codespaces", "version": "release-2"})
    result = fleet.fleet_status(now=10**12)
    assert result["stale_count"] == 1
    assert result["instance_count"] == 1


def test_heartbeat_requires_server_side_fleet_secret(monkeypatch):
    app = Flask(__name__)
    app.register_blueprint(agent_environments_bp)
    monkeypatch.setenv("NOUS_FLEET_TOKEN", "test-only-fleet-secret")
    payload = {"instance_id": "nous-vercel-02", "provider": "vercel", "version": "release-1"}
    client = app.test_client()
    assert client.post("/api/agent-environments/fleet/heartbeat", json=payload).status_code == 403
    response = client.post("/api/agent-environments/fleet/heartbeat", json=payload, headers={"X-NOUS-FLEET-TOKEN": "test-only-fleet-secret"})
    assert response.status_code == 200


def test_heartbeat_client_requires_https_and_stable_identity(monkeypatch):
    monkeypatch.setenv("NOUS_FLEET_COORDINATOR_URL", "http://coordinator.example")
    monkeypatch.setenv("NOUS_FLEET_TOKEN", "secret")
    monkeypatch.setenv("NOUS_FLEET_INSTANCE_ID", "nous-test-01")
    result = fleet_agent.send_heartbeat(force=True)
    assert result["skipped"] is True
    assert result["reason"] == "coordinator_must_be_https"


def test_heartbeat_client_sends_only_metadata(monkeypatch):
    monkeypatch.setenv("NOUS_FLEET_COORDINATOR_URL", "https://coordinator.example")
    monkeypatch.setenv("NOUS_FLEET_TOKEN", "secret")
    monkeypatch.setenv("NOUS_FLEET_INSTANCE_ID", "nous-test-01")
    seen = {}

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _limit):
            return b'{"ok":true,"desired_version":"release-2","update_available":true}'

    def fake_urlopen(req, timeout):
        seen["url"] = req.full_url
        seen["headers"] = dict(req.header_items())
        seen["body"] = json.loads(req.data.decode("utf-8"))
        seen["timeout"] = timeout
        return Response()

    monkeypatch.setattr(fleet_agent.urllib.request, "urlopen", fake_urlopen)
    result = fleet_agent.send_heartbeat(force=True)
    assert result["ok"] is True
    assert result["update_available"] is True
    assert seen["url"] == "https://coordinator.example/api/agent-environments/fleet/heartbeat"
    assert set(seen["body"]) == {"instance_id", "provider", "version", "commit_sha", "status"}
    assert "secret" not in json.dumps(seen["body"])
    assert seen["timeout"] <= 2


def test_rollout_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("NOUS_FLEET_AUTO_DEPLOY", raising=False)
    result = fleet_rollout.reconcile_and_dispatch()
    assert result["ok"] is True
    assert result["enabled"] is False
    assert result["reason"] == "automatic_rollout_disabled"


def test_rollout_queues_and_dispatches_one_explicit_render_target(monkeypatch):
    monkeypatch.setenv("NOUS_FLEET_AUTO_DEPLOY", "true")
    monkeypatch.setenv("NOUS_FLEET_DEPLOY_TARGETS", json.dumps({
        "nous-render-01": {"provider": "render", "service_id": "srv_12345", "enabled": True}
    }))
    monkeypatch.setenv("RENDER_API_KEY", "test-api-key")
    fleet.record_heartbeat({
        "instance_id": "nous-render-01", "provider": "render",
        "version": "release-1", "status": "healthy",
    })
    calls = []
    monkeypatch.setattr(fleet_rollout, "_request_render", lambda service_id: calls.append(service_id) or {"ok": True, "status_code": 202})
    result = fleet_rollout.reconcile_and_dispatch()
    assert result["ok"] is True
    assert result["dispatched"] is True
    assert result["state"] == "requested"
    assert calls == ["srv_12345"]
    assert fleet_rollout.rollout_status()["counts"]["requested"] == 1


def test_rollout_rejects_arbitrary_vercel_urls(monkeypatch):
    monkeypatch.setenv("NOUS_FLEET_DEPLOY_TARGETS", json.dumps({
        "nous-vercel-01": {"provider": "vercel", "deploy_hook_url": "https://evil.example/hook", "enabled": True}
    }))
    _targets, error = fleet_rollout._targets()
    assert error == "invalid_vercel_deploy_hook"
