"""Regression tests για brain planning και mission lifecycle."""

import importlib


def test_brain_plan_is_proposal_first(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import executor.autonomous_agent as agent
    agent = importlib.reload(agent)

    result = agent.run_agent("review the workspace")
    assert result["ok"] is True
    assert result["steps"][-1] == "request approval for changes"
    assert agent.pending_proposals()["proposals"] == []


def test_mission_blocks_approval_required_task(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import executor.mission_system as missions
    missions = importlib.reload(missions)

    mission = missions.create_mission("Deploy", tasks=[{"title": "deploy", "action": "deploy_vercel_test_app"}])
    result = missions.run_next_mission_task(mission["id"])

    assert result["ok"] is False
    assert result["approval_required"] is True
    assert result["mission"]["status"] == "blocked"
    assert result["task"]["status"] == "waiting_approval"


def test_mission_safe_task_progresses(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import executor.mission_system as missions
    missions = importlib.reload(missions)
    monkeypatch.setattr(missions, "run_ops_action", lambda action, payload=None: {"ok": True, "action": action})

    mission = missions.create_mission("Health", tasks=[{"title": "health", "action": "code_health"}])
    result = missions.run_next_mission_task(mission["id"])

    assert result["ok"] is True
    assert result["task"]["status"] == "done"


def test_approved_mission_task_executes_and_completes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import executor.mission_system as missions
    missions = importlib.reload(missions)
    calls = []
    monkeypatch.setattr(
        missions,
        "run_ops_action",
        lambda action, payload=None: calls.append((action, payload)) or {"ok": True},
    )

    mission = missions.create_mission(
        "Approved deploy",
        tasks=[{
            "title": "deploy",
            "action": "deploy_vercel_test_app",
            "payload": {"environment": "test"},
        }],
    )
    waiting = missions.run_next_mission_task(mission["id"])
    assert waiting["approval_required"] is True
    assert calls == []

    approved = missions.approve_task(mission["id"], waiting["task"]["id"])
    assert approved["ok"] is True
    result = missions.run_next_mission_task(mission["id"])

    assert result["ok"] is True
    assert calls == [("deploy_vercel_test_app", {"environment": "test"})]
    assert result["task"]["status"] == "done"
    assert result["mission"]["status"] == "done"


def test_rejected_mission_task_never_executes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import executor.mission_system as missions
    missions = importlib.reload(missions)
    calls = []
    monkeypatch.setattr(
        missions,
        "run_ops_action",
        lambda action, payload=None: calls.append(action) or {"ok": True},
    )

    mission = missions.create_mission(
        "Rejected deploy",
        tasks=[{"title": "deploy", "action": "deploy_vercel_test_app"}],
    )
    waiting = missions.run_next_mission_task(mission["id"])
    rejected = missions.reject_task(mission["id"], waiting["task"]["id"])
    result = missions.run_next_mission_task(mission["id"])

    assert rejected["ok"] is True
    assert result["ok"] is True
    assert result.get("idle") is True
    assert calls == []
    stored = missions.list_missions()[-1]
    assert stored["tasks"][0]["status"] == "rejected"


def test_unknown_mission_action_is_blocked_without_execution(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import executor.mission_system as missions
    missions = importlib.reload(missions)
    calls = []
    monkeypatch.setattr(
        missions,
        "run_ops_action",
        lambda action, payload=None: calls.append(action) or {"ok": True},
    )

    mission = missions.create_mission(
        "Unknown action",
        tasks=[{"title": "unsafe", "action": "arbitrary_shell"}],
    )
    result = missions.run_next_mission_task(mission["id"])

    assert result["ok"] is False
    assert result["blocked"] is True
    assert calls == []
