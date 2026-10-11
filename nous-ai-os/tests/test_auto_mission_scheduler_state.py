import json

import pytest

from executor import auto_mission_scheduler as scheduler


def test_corrupt_state_is_reported_and_never_overwritten(tmp_path, monkeypatch):
    path = tmp_path / "data" / "auto_mission_scheduler.json"
    monkeypatch.setattr(scheduler, "FILE", path)
    path.parent.mkdir(parents=True)
    original = b'{"enabled":'
    path.write_bytes(original)

    status = scheduler.auto_mission_scheduler_status()
    result = scheduler.start_auto_mission_scheduler(900)

    assert status["ok"] is False
    assert status["status"] == "unavailable"
    assert result == {"ok": False, "error": "auto_mission_scheduler_state_unavailable"}
    assert path.read_bytes() == original


def test_invalid_state_shape_is_rejected_without_repair(tmp_path, monkeypatch):
    path = tmp_path / "data" / "auto_mission_scheduler.json"
    monkeypatch.setattr(scheduler, "FILE", path)
    path.parent.mkdir(parents=True)
    original = json.dumps({"enabled": True, "interval_seconds": 1, "ticks": -1}).encode()
    path.write_bytes(original)

    with pytest.raises(ValueError, match="auto_mission_scheduler_state_invalid"):
        scheduler._load()
    assert path.read_bytes() == original


def test_state_save_is_atomic_and_validates_interval(tmp_path, monkeypatch):
    path = tmp_path / "data" / "auto_mission_scheduler.json"
    monkeypatch.setattr(scheduler, "FILE", path)
    state = scheduler._default_state()
    scheduler._save(state)

    assert json.loads(path.read_text(encoding="utf-8"))["interval_seconds"] == 900
    assert list(path.parent.glob(".auto_mission_scheduler.json.*.tmp")) == []
    with pytest.raises(ValueError, match="auto_mission_scheduler_state_invalid"):
        scheduler._save({**state, "interval_seconds": 10})


def test_manual_tick_does_not_run_when_state_is_corrupt(tmp_path, monkeypatch):
    path = tmp_path / "data" / "auto_mission_scheduler.json"
    monkeypatch.setattr(scheduler, "FILE", path)
    path.parent.mkdir(parents=True)
    original = b"not-json"
    path.write_bytes(original)
    monkeypatch.setattr(
        scheduler,
        "run_auto_mission_executor",
        lambda **_kwargs: pytest.fail("must not execute with corrupt scheduler state"),
    )

    result = scheduler.run_auto_mission_scheduler_once()

    assert result["ok"] is False
    assert result["error"] == "auto_mission_scheduler_state_unavailable"
    assert path.read_bytes() == original
