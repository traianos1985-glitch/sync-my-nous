import importlib

from executor.mission_contracts import (
    build_execution_evidence,
    build_plan_contract,
    verify_execution_evidence,
    verify_plan_contract,
)


def _task(task_id=1, action="code_health", payload=None):
    return {
        "id": task_id,
        "title": "health check",
        "action": action,
        "payload": payload or {},
        "requires_approval": False,
        "status": "pending",
        "result": None,
    }


def test_plan_contract_ignores_runtime_state_but_detects_intent_change():
    task = _task()
    contract = build_plan_contract([task])
    task["status"] = "running"
    task["started"] = 123.0
    assert verify_plan_contract(contract, [task])["ok"] is True
    task["action"] = "arbitrary_shell"
    result = verify_plan_contract(contract, [task])
    assert result["ok"] is False
    assert result["error"] == "mission_plan_changed"


def test_plan_contract_rejects_duplicate_task_ids():
    contract = build_plan_contract([_task(1), _task(1, "git_status")])
    assert contract["valid"] is False
    assert verify_plan_contract(contract, [_task(1), _task(1, "git_status")])["ok"] is False


def test_execution_evidence_verifies_outcome_and_detects_tampering():
    task = _task()
    task["status"] = "done"
    evidence = build_execution_evidence(task, {"ok": True, "value": 3}, "claim-123")
    assert verify_execution_evidence(evidence)["ok"] is True
    evidence["action"] = "arbitrary_shell"
    assert verify_execution_evidence(evidence)["ok"] is False


def test_execution_evidence_rejects_inconsistent_status():
    task = _task()
    task["status"] = "failed"
    evidence = build_execution_evidence(task, {"ok": False}, "claim-456")
    assert verify_execution_evidence(evidence)["ok"] is True
    evidence["task_status"] = "done"
    assert verify_execution_evidence(evidence)["ok"] is False


def test_mission_plan_mutation_blocks_action_before_execution(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import executor.mission_system as mission_module
    missions = importlib.reload(mission_module)
    calls = []
    monkeypatch.setattr(missions, "run_ops_action", lambda action, payload=None: calls.append(action) or {"ok": True})
    mission = missions.create_mission("Guarded plan", tasks=[{"title": "health", "action": "code_health"}])
    stored = missions.list_missions()[0]
    stored["tasks"][0]["action"] = "arbitrary_shell"
    missions._save([stored])
    result = missions.run_next_mission_task(mission["id"])
    assert result["ok"] is False
    assert result["error"] == "mission_plan_integrity_failure"
    assert calls == []


def test_successful_mission_task_has_verifiable_execution_evidence(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import executor.mission_system as mission_module
    missions = importlib.reload(mission_module)
    monkeypatch.setattr(missions, "run_ops_action", lambda action, payload=None: {"ok": True, "action": action})
    mission = missions.create_mission("Evidence plan", tasks=[{"title": "health", "action": "code_health"}])
    result = missions.run_next_mission_task(mission["id"])
    evidence = result["task"]["execution_evidence"]
    assert result["execution_ok"] is True
    assert verify_execution_evidence(evidence)["ok"] is True
