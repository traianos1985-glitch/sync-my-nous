import os

from executor import fleet_coordinator as fleet


def setup_function():
    fleet.clear_fleet_registry_for_tests()
    os.environ["NOUS_FLEET_DB_PATH"] = str(fleet._database_path().parent / "fleet-test.sqlite3")
    fleet.clear_fleet_registry_for_tests()
    os.environ["NOUS_FLEET_TARGET_VERSION"] = "release-2"
    os.environ["NOUS_VERSION"] = "release-2"


def teardown_function():
    fleet.clear_fleet_registry_for_tests()
    os.environ.pop("NOUS_FLEET_TARGET_VERSION", None)
    os.environ.pop("NOUS_FLEET_DB_PATH", None)
    os.environ.pop("NOUS_VERSION", None)


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


def test_rejects_invalid_metadata_and_unbounded_registry_growth():
    assert fleet.record_heartbeat({"instance_id": "x", "provider": "vercel", "version": "v1"})["error"] == "invalid_instance_id"
    assert fleet.record_heartbeat({"instance_id": "nous-valid-01", "provider": "https://evil.example", "version": "v1"})["error"] == "invalid_provider"


def test_target_version_missing_disables_drift_claims():
    os.environ.pop("NOUS_FLEET_TARGET_VERSION", None)
    os.environ.pop("NOUS_VERSION", None)
    result = fleet.record_heartbeat({"instance_id": "nous-unknown-01", "provider": "generic", "version": "v1"})
    assert result["ok"] is True
    assert result["update_available"] is False
    assert result["desired_version"] is None


def test_status_marks_stale_instances_without_deleting_them():
    fleet.record_heartbeat({"instance_id": "nous-codespaces-01", "provider": "codespaces", "version": "release-2"})
    result = fleet.fleet_status(now=10**12)
    assert result["stale_count"] == 1
    assert result["instance_count"] == 1


def test_heartbeat_requires_server_side_fleet_secret(client, monkeypatch):
    from executor.blueprints.fleet_bp import fleet_bp
    from flask import Flask

    app = Flask(__name__)
    app.register_blueprint(fleet_bp)
    monkeypatch.setenv("NOUS_FLEET_TOKEN", "test-only-fleet-secret")
    payload = {"instance_id": "nous-vercel-02", "provider": "vercel", "version": "release-1"}
    assert app.test_client().post("/api/fleet/heartbeat", json=payload).status_code == 403
    response = app.test_client().post("/api/fleet/heartbeat", json=payload, headers={"X-NOUS-FLEET-TOKEN": "test-only-fleet-secret"})
    assert response.status_code == 200
