from executor.mission_contracts import build_execution_evidence, build_plan_contract
from executor.mission_integrity import audit_missions


def _mission(mission_id=1, task_id=1, now=10000.0):
    task = {
        "id": task_id,
        "title": "health",
        "action": "code_health",
        "payload": {},
        "requires_approval": False,
        "status": "done",
        "started": now - 2,
        "finished": now - 1,
        "execution_id": f"exec-{task_id}",
        "result": {"ok": True, "value": "healthy"},
    }
    task["execution_evidence"] = build_execution_evidence(task, task["result"], task["execution_id"])
    mission = {
        "id": mission_id,
        "title": "health check",
        "status": "done",
        "tasks": [task],
    }
    mission["plan_contract"] = build_plan_contract(mission["tasks"])
    return mission


def test_valid_completed_mission_is_healthy():
    report = audit_missions([_mission()], now=10000.0)
    assert report["ok"] is True
    assert report["issue_count"] == 0


def test_duplicate_mission_and_task_ids_are_reported():
    first = _mission(1, 1)
    second = _mission(1, 1)
    report = audit_missions([first, second], now=10000.0)
    codes = {issue["code"] for issue in report["issues"]}
    assert "duplicate_mission_id" in codes
    assert "duplicate_task_id" in codes


def test_done_mission_with_mutated_result_is_degraded():
    mission = _mission()
    mission["tasks"][0]["result"]["value"] = "mutated"
    report = audit_missions([mission], now=10000.0)
    codes = {issue["code"] for issue in report["issues"]}
    assert report["status"] == "degraded"
    assert "done_task_evidence_invalid" in codes
    assert "done_mission_not_verified" in codes


def test_stale_running_claim_is_a_warning():
    mission = _mission()
    task = mission["tasks"][0]
    task["status"] = "running"
    task["started"] = 100.0
    task.pop("execution_evidence")
    mission["status"] = "active"
    mission.pop("plan_contract", None)
    report = audit_missions([mission], now=10000.0, stale_after=900)
    assert any(issue["code"] == "stale_or_invalid_running_claim" for issue in report["issues"])
    assert report["warning_count"] >= 1


def test_plan_contract_mismatch_is_reported():
    mission = _mission()
    mission["tasks"][0]["action"] = "arbitrary_shell"
    report = audit_missions([mission], now=10000.0)
    assert any(issue["code"] == "mission_plan_contract_mismatch" for issue in report["issues"])


def test_non_list_store_fails_closed():
    report = audit_missions({"not": "a list"})
    assert report["ok"] is False
    assert report["issues"][0]["code"] == "mission_store_not_a_list"
