import pytest
from flask import Flask

from executor import fleet_coordinator as fleet
from executor.blueprints.agent_environments_bp import agent_environments_bp


@pytest.fixture(autouse=True)
def isolated_registry(tmp_path, monkeypatch):
    monkeypatch.setenv("NOUS_FLEET_DB_PATH", str(tmp_path / "fleet-test.sqlite3"))
    monkeypatch.setenv("NOUS_FLEET_TARGET_VERSION", "release-2")
    monkeypatch.setenv("NOUS_VERSION", "release-2")
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


def test_full_commit_sha_matching_is_exact_and_short_target_fails_closed(monkeypatch):
    full_sha = "a" * 40
    monkeypatch.setenv("NOUS_FLEET_TARGET_VERSION", full_sha)
    exact = fleet.record_heartbeat({
        "instance_id": "nous-sha-exact-01", "provider": "render",
        "version": full_sha, "commit_sha": full_sha, "status": "healthy",
    })
    assert exact["update_available"] is False

    monkeypatch.setenv("NOUS_FLEET_TARGET_VERSION", "a" * 12)
    short_target = fleet.record_heartbeat({
        "instance_id": "nous-sha-short-01", "provider": "render",
        "version": full_sha, "commit_sha": full_sha, "status": "healthy",
    })
    assert short_target["update_available"] is True


def test_full_commit_sha_matching_rejects_same_length_mismatch(monkeypatch):
    monkeypatch.setenv("NOUS_FLEET_TARGET_VERSION", "a" * 40)
    result = fleet.record_heartbeat({
        "instance_id": "nous-sha-mismatch-01", "provider": "render",
        "version": "b" * 40, "commit_sha": "b" * 40, "status": "healthy",
    })
    assert result["update_available"] is True


def test_degraded_fleet_health_requires_three_consecutive_successes():
    payload = {
        "instance_id": "nous-health-hysteresis-01",
        "provider": "render",
        "version": "release-2",
    }
    fleet.record_heartbeat({**payload, "status": "healthy"})
    fleet.record_heartbeat({**payload, "status": "degraded"})
    status = fleet.fleet_status()
    instance = status["instances"][0]
    assert instance["reported_status"] == "degraded"
    assert instance["last_reported_status"] == "degraded"
    assert instance["failure_count"] == 1

    for expected_streak in (1, 2):
        fleet.record_heartbeat({**payload, "status": "healthy"})
        instance = fleet.fleet_status()["instances"][0]
        assert instance["reported_status"] == "degraded"
        assert instance["healthy_streak"] == expected_streak

    fleet.record_heartbeat({**payload, "status": "healthy"})
    instance = fleet.fleet_status()["instances"][0]
    assert instance["reported_status"] == "healthy"
    assert instance["healthy_streak"] == 3
    assert instance["failure_count"] == 1


def test_new_installation_health_state_migrates_existing_sqlite_schema(tmp_path, monkeypatch):
    import sqlite3

    db_path = tmp_path / "legacy-fleet.sqlite3"
    with sqlite3.connect(db_path) as connection:
        connection.execute("""CREATE TABLE fleet_instances (
            instance_id TEXT PRIMARY KEY, provider TEXT NOT NULL, version TEXT NOT NULL,
            commit_sha TEXT, status TEXT NOT NULL, first_seen REAL NOT NULL, last_seen REAL NOT NULL
        )""")
        connection.execute(
            "INSERT INTO fleet_instances VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("nous-legacy-01", "render", "release-2", None, "healthy", 1.0, 2.0),
        )
    monkeypatch.setenv("NOUS_FLEET_DB_PATH", str(db_path))

    status = fleet.fleet_status()
    assert status["instance_count"] == 1
    assert status["instances"][0]["reported_status"] == "unknown"
    fleet.record_heartbeat({
        "instance_id": "nous-legacy-01", "provider": "render",
        "version": "release-2", "status": "healthy",
    })
    assert fleet.fleet_status()["instances"][0]["reported_status"] == "healthy"
