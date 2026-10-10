import importlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from executor import goal_system, personal_agent


@pytest.mark.parametrize("module_name,file_name,operation", [
    ("goal_system", "goals_v2.json", "goal"),
    ("personal_agent", "personal_agent.json", "personal"),
])
@pytest.mark.parametrize("raw", [b'{"broken":', b'{"not":"the expected shape"}', b'[{"valid":true}]'])
def test_goal_and_personal_state_fail_closed_without_overwrite(
    tmp_path, monkeypatch, module_name, file_name, operation, raw
):
    monkeypatch.chdir(tmp_path)
    module = importlib.reload(goal_system if module_name == "goal_system" else personal_agent)
    if operation == "goal":
        monkeypatch.setattr(module, "FILE", f"data/{file_name}")
    else:
        monkeypatch.setattr(module, "DB", f"data/{file_name}")
    Path("data").mkdir()
    path = Path("data") / file_name
    path.write_bytes(raw)

    with pytest.raises(RuntimeError, match="json_state_integrity_failure"):
        if operation == "goal":
            module.create_goal("must preserve data")
        else:
            module.add_goal("must preserve data")
    assert path.read_bytes() == raw


def test_personal_agent_rejects_wrong_nested_shapes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module = importlib.reload(personal_agent)
    monkeypatch.setattr(module, "DB", "data/personal_agent.json")
    Path("data").mkdir()
    raw = json.dumps({"profile": [], "goals": [], "projects": [], "decisions": []}).encode()
    Path("data/personal_agent.json").write_bytes(raw)
    with pytest.raises(RuntimeError, match="json_state_integrity_failure"):
        module.load_db()
    assert Path("data/personal_agent.json").read_bytes() == raw


def test_concurrent_goal_creation_and_personal_agent_writes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    goals = importlib.reload(goal_system)
    personal = importlib.reload(personal_agent)
    monkeypatch.setattr(goals, "FILE", "data/goals_v2.json")
    monkeypatch.setattr(personal, "DB", "data/personal_agent.json")

    with ThreadPoolExecutor(max_workers=8) as pool:
        created_goals = list(pool.map(lambda i: goals.create_goal(f"goal-{i}"), range(30)))
    assert len(goals.list_goals()) == len(created_goals) == 30
    assert len({str(goal["id"]) for goal in created_goals}) == 30

    with ThreadPoolExecutor(max_workers=8) as pool:
        created_projects = list(pool.map(personal.add_project, [f"project-{i}" for i in range(30)]))
    state = personal.load_db()
    assert len(state["projects"]) == len(created_projects) == 30
    assert len({str(item["id"]) for item in created_projects}) == 30


def test_seed_core_goals_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module = importlib.reload(goal_system)
    monkeypatch.setattr(module, "FILE", "data/goals_v2.json")
    first = module.seed_core_goals()
    second = module.seed_core_goals()
    assert len(first["created"]) == 4
    assert second["created"] == []
    assert len(second["goals"]) == 4
