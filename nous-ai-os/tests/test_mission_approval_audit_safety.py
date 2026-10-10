import importlib
import json

from executor import mission_system


def _fresh(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module = importlib.reload(mission_system)
    monkeypatch.setattr(module, "FILE", "data/missions.json")
    monkeypatch.setattr(module, "write_journal", lambda *_args, **_kwargs: {"ok": True})
    return module


def test_approval_cannot_be_granted_before_task_enters_waiting_state(tmp_path, monkeypatch):
    missions = _fresh(tmp_path, monkeypatch)
    mission = missions.create_mission(
        "Deploy check",
        tasks=[{"action": "deploy_vercel_test_app", "payload": {}}],
    )
    task_id = mission["tasks"][0]["id"]

    result = missions.approve_task(mission["id"], task_id)

    assert result["ok"] is False
    assert result["error"] == "task_not_awaiting_approval"


def test_non_approval_action_cannot_be_marked_approved(tmp_path, monkeypatch):
    missions = _fresh(tmp_path, monkeypatch)
    mission = missions.create_mission("Safe check", tasks=[{"action": "code_health"}])
    task_id = mission["tasks"][0]["id"]

    result = missions.approve_task(mission["id"], task_id)

    assert result["ok"] is False
    assert result["error"] == "task_does_not_require_approval"


def test_approval_is_bound_to_action_and_payload_fingerprint(tmp_path, monkeypatch):
    missions = _fresh(tmp_path, monkeypatch)
    calls = []
    monkeypatch.setattr(missions, "run_ops_action", lambda action, payload=None: calls.append(action) or {"ok": True})
    mission = missions.create_mission(
        "Deploy check",
        tasks=[{"action": "deploy_vercel_test_app", "payload": {"environment": "test"}}],
    )
    task_id = mission["tasks"][0]["id"]
    waiting = missions.run_next_mission_task(mission["id"])
    assert waiting["approval_required"] is True

    approved = missions.approve_task(mission["id"], task_id)
    assert approved["ok"] is True
    assert approved["task"]["approved_intent_sha256"]

    # Simulate approval metadata tampering while leaving the immutable plan intact.
    with missions._edit_missions() as items:
        task = items[0]["tasks"][0]
        task["approved_intent_sha256"] = "0" * 64

    result = missions.run_next_mission_task(mission["id"])

    assert result["approval_required"] is True
    assert result["task"]["status"] == "waiting_approval"
    assert result["task"]["approved"] is False
    assert calls == []


def test_mission_payloads_are_bounded_and_invalid_payloads_rejected(tmp_path, monkeypatch):
    missions = _fresh(tmp_path, monkeypatch)

    too_large = missions.create_mission(
        "Too large",
        tasks=[{"action": "code_health", "payload": {"value": "x" * 40000}}],
    )
    too_many = missions.create_mission(
        "Too many",
        tasks=[{"action": "code_health"} for _ in range(101)],
    )

    assert too_large["ok"] is False
    assert too_large["error"] == "payload_too_large"
    assert too_many["ok"] is False
    assert too_many["error"] == "too_many_mission_tasks"


def test_audit_summary_does_not_copy_operational_values():
    from executor.audit_safety import audit_summary

    sensitive = {
        "ok": True,
        "result": {"api_key": "not-for-the-journal", "message": "private result text"},
        "action": "code_health",
    }
    summary = audit_summary(sensitive)
    encoded = json.dumps(summary)

    assert summary["ok"] is True
    assert summary["action"] == "code_health"
    assert "not-for-the-journal" not in encoded
    assert "private result text" not in encoded
    assert summary["value_types"]["result"] == "object"
