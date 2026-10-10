import importlib
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def test_auto_executor_records_failed_mission_as_failure(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import executor.auto_mission_executor as executor
    executor = importlib.reload(executor)

    monkeypatch.setattr(executor, "mission_status", lambda: {
        "missions": [{"id": "m1", "title": "bad", "status": "active", "tasks": [{"status": "pending", "action": "code_health"}]}]
    })
    monkeypatch.setattr(executor, "run_mission_cycle", lambda *_args: {"ok": False, "status": "failed_or_blocked", "results": []})
    monkeypatch.setattr(executor, "apply_goal_progress_intelligence", lambda: {"ok": True})
    monkeypatch.setattr(executor, "run_self_diagnosis", lambda: {"ok": True})
    lessons = []
    monkeypatch.setattr(executor, "record_decision", lambda **kwargs: None)
    monkeypatch.setattr(executor, "record_lesson", lambda **kwargs: lessons.append(kwargs))

    result = executor.run_auto_mission_executor()

    assert result["ok"] is False
    assert result["run"]["status"] == "failed"
    assert lessons[0]["outcome"] == "failure"
    persisted = json.loads(Path("data/auto_mission_executor.json").read_text(encoding="utf-8"))
    assert "run_in_progress" not in persisted


def test_auto_executor_rejects_overlapping_run(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import executor.auto_mission_executor as executor
    executor = importlib.reload(executor)

    entered = threading.Event()
    release = threading.Event()
    monkeypatch.setattr(executor, "mission_status", lambda: {
        "missions": [{"id": "m1", "title": "health", "status": "active", "tasks": [{"status": "pending", "action": "code_health"}]}]
    })

    def slow_cycle(*_args):
        entered.set()
        release.wait(timeout=2)
        return {"ok": True, "status": "completed", "results": []}

    monkeypatch.setattr(executor, "run_mission_cycle", slow_cycle)
    monkeypatch.setattr(executor, "apply_goal_progress_intelligence", lambda: {"ok": True})
    monkeypatch.setattr(executor, "run_self_diagnosis", lambda: {"ok": True})
    monkeypatch.setattr(executor, "record_decision", lambda **kwargs: None)
    monkeypatch.setattr(executor, "record_lesson", lambda **kwargs: None)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(executor.run_auto_mission_executor)
        assert entered.wait(timeout=2)
        second = executor.run_auto_mission_executor()
        assert second["error"] == "run_already_in_progress"
        release.set()
        completed = first.result(timeout=3)

    assert completed["run"]["status"] == "completed"
