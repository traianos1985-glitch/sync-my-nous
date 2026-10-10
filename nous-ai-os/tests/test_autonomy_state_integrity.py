import importlib
import json
from pathlib import Path


def test_corrupt_autonomy_state_is_reported_and_not_overwritten(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from executor import autonomy_service

    service = importlib.reload(autonomy_service)
    Path("data").mkdir()
    original = b'{"enabled": "maybe", "interval": 300}'
    Path(service.STATE_FILE).write_bytes(original)

    assert service.status()["status"] == "degraded"
    assert service.watchdog_check()["reason"] == "autonomy_state_integrity_failure"
    result = service.run_cycle()
    assert result["ok"] is False
    assert result["error"] == "autonomy_state_integrity_failure"
    assert Path(service.STATE_FILE).read_bytes() == original


def test_autonomy_interval_is_bounded(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from executor import autonomy_service

    service = importlib.reload(autonomy_service)
    assert service.enable(30)["interval"] == 30
    for invalid in (0, -1, 86401, "not-a-number"):
        try:
            service.enable(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(f"interval should have been rejected: {invalid}")


def test_cycle_lock_reports_busy_without_starting_second_cycle(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from executor import autonomy_service

    service = importlib.reload(autonomy_service)
    Path("data").mkdir()
    with open(service.STATE_FILE + ".cycle.lock", "a", encoding="utf-8") as lock_handle:
        import fcntl
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        try:
            result = service.run_cycle()
        finally:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)

    assert result["busy"] is True
    assert result["error"] == "autonomy_cycle_already_running"


def test_state_save_is_valid_json_and_contains_defaults(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from executor import autonomy_service

    service = importlib.reload(autonomy_service)
    state = service.enable(45)
    persisted = json.loads(Path(service.STATE_FILE).read_text(encoding="utf-8"))
    assert persisted["enabled"] is True
    assert persisted["interval"] == 45
    assert state["cycles"] == 0
