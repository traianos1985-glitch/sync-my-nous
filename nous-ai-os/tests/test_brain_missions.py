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
