import importlib
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from executor import mission_system


def _fresh_missions(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module = importlib.reload(mission_system)
    monkeypatch.setattr(module, "FILE", "data/missions.json")
    return module


def test_parallel_workers_claim_a_task_only_once(tmp_path, monkeypatch):
    missions = _fresh_missions(tmp_path, monkeypatch)
    calls = []

    def slow_action(action, payload=None):
        calls.append(action)
        time.sleep(0.08)
        return {"ok": True, "action": action}

    monkeypatch.setattr(missions, "run_ops_action", slow_action)
    mission = missions.create_mission("One task", tasks=[{"action": "code_health"}])
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: missions.run_next_mission_task(mission["id"]), range(2)))

    assert calls == ["code_health"]
    assert sum(bool(result.get("execution_ok")) for result in results) == 1
    assert any(result.get("idle") or result.get("busy") for result in results)


def test_parallel_worker_cannot_skip_a_running_task_and_start_the_next(tmp_path, monkeypatch):
    missions = _fresh_missions(tmp_path, monkeypatch)
    entered = threading.Event()
    release = threading.Event()
    calls = []

    def slow_action(action, payload=None):
        calls.append(action)
        entered.set()
        release.wait(timeout=2)
        return {"ok": True, "action": action}

    monkeypatch.setattr(missions, "run_ops_action", slow_action)
    mission = missions.create_mission("Sequential tasks", tasks=[
        {"action": "code_health"},
        {"action": "git_status"},
    ])

    with ThreadPoolExecutor(max_workers=1) as pool:
        first = pool.submit(missions.run_next_mission_task, mission["id"])
        assert entered.wait(timeout=2)
        second = missions.run_next_mission_task(mission["id"])
        assert second["busy"] is True
        assert calls == ["code_health"]
        release.set()
        assert first.result(timeout=3)["execution_ok"] is True

    next_result = missions.run_next_mission_task(mission["id"])
    assert next_result["execution_ok"] is True
    assert calls == ["code_health", "git_status"]


def test_action_exception_is_recorded_as_failure_not_success(tmp_path, monkeypatch):
    missions = _fresh_missions(tmp_path, monkeypatch)
    monkeypatch.setattr(missions, "run_ops_action", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")))
    mission = missions.create_mission("Failing task", tasks=[{"action": "code_health"}])

    result = missions.run_next_mission_task(mission["id"])

    assert result["ok"] is False
    assert result["execution_ok"] is False
    assert result["task"]["status"] == "failed"
    assert result["task"]["result"]["error"] == "action_execution_exception"
    assert result["mission"]["status"] == "blocked"


def test_mission_cycle_reports_failure_and_does_not_continue(tmp_path, monkeypatch):
    missions = _fresh_missions(tmp_path, monkeypatch)
    calls = []
    monkeypatch.setattr(missions, "run_ops_action", lambda action, payload=None: calls.append(action) or {"ok": False, "error": "check_failed"})
    mission = missions.create_mission("Failed cycle", tasks=[
        {"action": "code_health"},
        {"action": "git_status"},
    ])

    result = missions.run_mission_cycle(mission["id"], max_steps=5)

    assert result["ok"] is False
    assert result["status"] == "failed_or_blocked"
    assert len(result["results"]) == 1
    assert calls == ["code_health"]
    assert missions.list_missions()[-1]["tasks"][0]["status"] == "failed"


def test_concurrent_mission_creation_does_not_lose_records(tmp_path, monkeypatch):
    missions = _fresh_missions(tmp_path, monkeypatch)
    with ThreadPoolExecutor(max_workers=8) as pool:
        created = list(pool.map(lambda index: missions.create_mission(f"mission-{index}"), range(40)))
    stored = missions.list_missions()
    assert len(created) == 40
    assert len(stored) == 40
    assert len({str(item["id"]) for item in stored}) == 40
    assert Path("data/missions.json.lock").exists()


def test_approval_cannot_change_a_task_after_execution_claim(tmp_path, monkeypatch):
    missions = _fresh_missions(tmp_path, monkeypatch)
    monkeypatch.setattr(missions, "run_ops_action", lambda *_args, **_kwargs: {"ok": True})
    mission = missions.create_mission("Approved task", tasks=[{"action": "deploy_vercel_test_app"}])
    waiting = missions.run_next_mission_task(mission["id"])
    assert waiting["approval_required"] is True
    approved = missions.approve_task(mission["id"], waiting["task"]["id"])
    assert approved["ok"] is True
    done = missions.run_next_mission_task(mission["id"])
    assert done["execution_ok"] is True
    assert missions.approve_task(mission["id"], waiting["task"]["id"])["error"] == "task_not_awaiting_approval"
