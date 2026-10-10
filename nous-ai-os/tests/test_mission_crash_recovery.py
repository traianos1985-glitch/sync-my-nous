import importlib
import json
from pathlib import Path


def _module(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import executor.mission_system as mission_system
    return importlib.reload(mission_system)


def test_recovery_quarantines_stale_running_task_without_retry(tmp_path, monkeypatch):
    missions = _module(tmp_path, monkeypatch)
    now = 10_000.0
    mission = {
        "id": "m1",
        "title": "interrupted",
        "status": "active",
        "updated": now - 1000,
        "tasks": [{
            "id": "t1",
            "title": "deploy",
            "action": "deploy_vercel_test_app",
            "payload": {},
            "status": "running",
            "started": now - 1200,
            "execution_id": "claim-123",
            "result": None,
        }, {
            "id": "t2",
            "title": "later task",
            "action": "code_health",
            "payload": {},
            "status": "pending",
            "result": None,
        }],
        "plan_contract": None,
    }
    # Give the mission a valid baseline contract so the test isolates recovery.
    from executor.mission_contracts import build_plan_contract
    mission["plan_contract"] = build_plan_contract(mission["tasks"])
    missions._save([mission])
    calls = []
    monkeypatch.setattr(missions, "run_ops_action", lambda *args, **kwargs: calls.append(args) or {"ok": True})
    report = missions.recover_interrupted_missions(stale_after=900, now=now)
    saved = missions.list_missions()[0]
    assert report["recovered_count"] == 1
    assert report["automatic_retries"] == 0
    assert saved["tasks"][0]["status"] == "needs_review"
    assert saved["tasks"][0]["recovery_evidence"]["execution_id"] == "claim-123"
    assert saved["status"] == "blocked"
    result = missions.run_next_mission_task("m1")
    assert result["needs_review"] is True
    assert calls == []
    assert saved["tasks"][1]["status"] == "pending"


def test_recovery_ignores_recent_or_future_running_claims(tmp_path, monkeypatch):
    missions = _module(tmp_path, monkeypatch)
    now = 5000.0
    mission = {
        "id": "m2",
        "status": "active",
        "tasks": [
            {"id": "recent", "status": "running", "started": now - 30, "execution_id": "r1"},
            {"id": "future", "status": "running", "started": now + 60, "execution_id": "f1"},
        ],
    }
    missions._save([mission])
    report = missions.recover_interrupted_missions(stale_after=900, now=now)
    assert report["recovered_count"] == 0
    assert [task["status"] for task in missions.list_missions()[0]["tasks"]] == ["running", "running"]


def test_recovery_is_idempotent_and_keeps_original_claim_id(tmp_path, monkeypatch):
    missions = _module(tmp_path, monkeypatch)
    now = 9000.0
    missions._save([{
        "id": "m3",
        "status": "active",
        "tasks": [{"id": "t3", "status": "running", "started": now - 2000, "execution_id": "original"}],
    }])
    first = missions.recover_interrupted_missions(now=now)
    second = missions.recover_interrupted_missions(now=now + 100)
    task = missions.list_missions()[0]["tasks"][0]
    assert first["recovered_count"] == 1
    assert second["recovered_count"] == 0
    assert task["status"] == "needs_review"
    assert task["execution_id"] == "original"
