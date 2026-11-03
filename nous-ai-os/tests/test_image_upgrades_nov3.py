"""External 24/7 scheduler tick, storage durability report and honest companion status."""
import importlib
import time

import pytest


@pytest.fixture
def autonomy(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("NOUS_AUTONOMY_ENABLED_DEFAULT", raising=False)
    monkeypatch.delenv("NOUS_AUTONOMY_INTERVAL", raising=False)
    from executor import autonomy_service

    service = importlib.reload(autonomy_service)
    calls = []
    monkeypatch.setattr(service, "run_once", lambda: calls.append("run_once") or {"ran": True})
    monkeypatch.setattr(service, "auto_learning_cycle", lambda: {"ok": True})
    monkeypatch.setattr(service, "master_cycle", lambda real_research=False: {"ok": True})
    monkeypatch.setattr(service, "scan_if_due", lambda: {"ran": False})
    monkeypatch.setattr(service, "battery_guard", lambda: {"ok": True})
    service._test_calls = calls
    yield service
    service.stop_loop("test_teardown", timeout=5)


def test_external_tick_skips_when_disabled(autonomy):
    result = autonomy.external_tick()
    assert result["ran"] is False and result["reason"] == "disabled"
    assert autonomy._test_calls == []


def test_external_tick_runs_once_then_waits_for_interval(autonomy):
    autonomy.enable(600)
    first = autonomy.external_tick()
    assert first["ran"] is True
    assert first["loop_running"] is True
    second = autonomy.external_tick()
    assert second["ran"] is False and second["reason"] == "not_due"
    assert 0 < second["next_due_in"] <= 600
    assert autonomy._test_calls.count("run_once") == 1


def test_external_tick_respects_emergency_stop(autonomy):
    autonomy.enable(600)
    autonomy.emergency_stop("test")
    result = autonomy.external_tick()
    assert result["ran"] is False and result["reason"] == "emergency_stop"
    assert autonomy._test_calls == []


def test_fresh_disk_stays_disabled_without_opt_in(autonomy):
    assert autonomy.status()["enabled"] is False


def test_fresh_disk_enables_when_operator_opts_in(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NOUS_AUTONOMY_ENABLED_DEFAULT", "1")
    monkeypatch.setenv("NOUS_AUTONOMY_INTERVAL", "900")
    from executor import autonomy_service

    service = importlib.reload(autonomy_service)
    monkeypatch.setattr(service, "battery_guard", lambda: {"ok": True})
    state = service.status()
    assert state["enabled"] is True and state["interval"] == 900


def test_invalid_default_interval_falls_back(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NOUS_AUTONOMY_INTERVAL", "2")
    from executor import autonomy_service

    service = importlib.reload(autonomy_service)
    assert service._default_state()["interval"] == service.DEFAULT_INTERVAL


def test_storage_report_flags_render_without_disk(tmp_path, monkeypatch):
    from executor.storage_durability import storage_report

    monkeypatch.setenv("RENDER", "true")
    monkeypatch.delenv("NOUS_PERSISTENT_STORAGE", raising=False)
    report = storage_report(str(tmp_path))
    assert report["mode"] == "ephemeral" and report["durable"] is False
    assert report["warning"]


def test_storage_report_trusts_explicit_declaration(tmp_path, monkeypatch):
    from executor.storage_durability import storage_report

    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("NOUS_PERSISTENT_STORAGE", "1")
    report = storage_report(str(tmp_path))
    assert report["durable"] is True and report["warning"] is None


def test_companion_unavailable_off_android_even_with_token(monkeypatch):
    from executor import companion_bridge

    monkeypatch.setenv("NOUS_COMPANION_PAIRING_TOKEN", "pair-test")
    monkeypatch.setattr(companion_bridge.shutil, "which", lambda name: None)
    status = companion_bridge.companion_status()
    assert status["pairing_configured"] is True
    assert status["available"] is False
    assert status["missing"] == ["android_host_required"]
    assert "pair-test" not in str(status)


def test_companion_available_on_android_with_token(monkeypatch):
    from executor import companion_bridge

    monkeypatch.setenv("NOUS_COMPANION_PAIRING_TOKEN", "pair-test")
    monkeypatch.setattr(companion_bridge.shutil, "which", lambda name: "/system/bin/am")
    assert companion_bridge.companion_status()["available"] is True


def _client(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NOUS_TOKEN", "test-master-token")
    from executor import router

    return router.app.test_client()


def test_cycle_route_requires_token(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    assert client.post("/remote/service/cycle").status_code == 401


def test_cycle_route_with_token(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    from executor import router

    monkeypatch.setattr(router, "service_external_tick", lambda: {"ok": True, "ran": False, "reason": "disabled"})
    response = client.post("/remote/service/cycle", headers={"Authorization": "Bearer test-master-token"})
    assert response.status_code == 200
    assert response.get_json()["reason"] == "disabled"


def test_storage_route_is_public_and_secret_free(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    body = client.get("/api/system/storage").get_json()
    assert body["ok"] is True and "durable" in body
    assert "test-master-token" not in str(body)
