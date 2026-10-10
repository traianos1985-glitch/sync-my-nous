import importlib

from executor.mission_completion import (
    find_explicit_failure,
    verify_mission_completion,
    verify_task_completion,
)
from executor.mission_contracts import build_execution_evidence, build_plan_contract


def _task(task_id=1, action="code_health", payload=None, result=None, status="done"):
    task = {
        "id": task_id,
        "title": "task",
        "action": action,
        "payload": payload or {},
        "status": status,
        "result": result if result is not None else {"ok": True, "value": "checked"},
        "execution_id": f"exec-{task_id}",
    }
    task["execution_evidence"] = build_execution_evidence(
        task, task["result"], task["execution_id"]
    )
    return task


def test_nested_explicit_failure_is_not_hidden_by_outer_success():
    result = {"ok": True, "result": {"health": {"ok": False, "error": "service_down"}}}
    failures = find_explicit_failure(result)
    assert any(item["reason"] == "ok_false" for item in failures)
    assert any(item["reason"] == "explicit_error" for item in failures)


def test_task_completion_accepts_consistent_evidence():
    assert verify_task_completion(_task())["status"] == "verified"


def test_task_completion_rejects_missing_evidence_for_review():
    task = _task()
    task.pop("execution_evidence")
    assert verify_task_completion(task)["reason"] == "execution_evidence_invalid"


def test_task_completion_detects_result_mutation():
    task = _task()
    task["result"]["value"] = "changed after execution"
    assessment = verify_task_completion(task)
    assert assessment["status"] == "needs_review"
    assert assessment["reason"] == "task_and_evidence_mismatch"


def test_task_completion_detects_payload_mutation():
    task = _task(payload={"path": "safe"})
    task["payload"]["path"] = "../outside"
    assert verify_task_completion(task)["status"] == "needs_review"


def test_task_completion_rejects_nested_failure_even_when_status_says_done():
    task = _task(result={"ok": True, "result": {"ok": False, "error": "operation failed"}})
    assessment = verify_task_completion(task)
    assert assessment["status"] == "failed"
    assert assessment["reason"] == "explicit_failure_in_result"


def test_mission_completion_requires_all_tasks_verified():
    mission = {"tasks": [_task(1), _task(2)]}
    assert verify_mission_completion(mission)["status"] == "completed"
    mission["tasks"][1].pop("execution_evidence")
    result = verify_mission_completion(mission)
    assert result["status"] == "needs_review"
    assert result["verified_count"] == 1
    assert result["review_count"] == 1


def test_failed_task_makes_mission_failed():
    task = _task(status="failed", result={"ok": False, "error": "nope"})
    mission = {"tasks": [task]}
    assert verify_mission_completion(mission)["status"] == "failed"


def test_mission_execution_does_not_mark_wrapped_nested_failure_done(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import executor.mission_system as mission_module
    missions = importlib.reload(mission_module)
    calls = []
    monkeypatch.setattr(
        missions,
        "run_ops_action",
        lambda action, payload=None: calls.append(action) or {
            "ok": True,
            "action": action,
            "result": {"ok": False, "error": "underlying subsystem failed"},
        },
    )
    mission = missions.create_mission(
        "Nested failure",
        tasks=[{"title": "health", "action": "code_health"}],
    )
    result = missions.run_next_mission_task(mission["id"])
    assert result["execution_ok"] is False
    assert result["task"]["status"] == "failed"
    assert result["mission"]["status"] == "blocked"
    assert calls == ["code_health"]


def test_successful_mission_has_completion_verification(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import executor.mission_system as mission_module
    missions = importlib.reload(mission_module)
    monkeypatch.setattr(
        missions,
        "run_ops_action",
        lambda action, payload=None: {"ok": True, "action": action, "result": {"value": "healthy"}},
    )
    mission = missions.create_mission(
        "Verified",
        tasks=[{"title": "health", "action": "code_health"}],
    )
    result = missions.run_next_mission_task(mission["id"])
    assert result["execution_ok"] is True
    assert result["mission"]["status"] == "done"
    assert result["mission"]["result"] == "all_tasks_verified"
    assert result["mission"]["completion_verification"]["status"] == "completed"
