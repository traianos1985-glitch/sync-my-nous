"""Regression tests for Fleet API authentication boundaries."""
import pytest

pytest.importorskip("flask")


def test_fleet_status_requires_admin_scope(monkeypatch):
    from executor import router
    from executor.blueprints import agent_environments_bp as fleet_bp

    monkeypatch.setattr(fleet_bp, "check_admin_token", lambda _request: False)
    monkeypatch.setattr(
        fleet_bp, "fleet_status",
        lambda: pytest.fail("fleet status must not be disclosed without admin scope"),
    )
    response = router.app.test_client().get(
        "/api/agent-environments/fleet/status",
        headers={"Authorization": "Bearer ordinary-user-token"},
    )
    assert response.status_code == 403
    assert response.get_json()["error"] == "admin_scope_required"


def test_fleet_heartbeat_requires_fleet_specific_auth(monkeypatch):
    from executor import router
    from executor.blueprints import agent_environments_bp as fleet_bp

    monkeypatch.setattr(fleet_bp, "_fleet_token_matches", lambda _payload: False)
    monkeypatch.setattr(
        fleet_bp, "record_heartbeat",
        lambda *_args, **_kwargs: pytest.fail("unauthenticated heartbeat must not be stored"),
    )
    response = router.app.test_client().post(
        "/api/agent-environments/fleet/heartbeat",
        json={"instance_id": "test-instance", "provider": "generic", "version": "1.0"},
    )
    assert response.status_code == 403
    assert response.get_json()["error"] == "fleet_authentication_required"
