import time
from executor.mission_system import create_mission, mission_status, run_mission_cycle
from executor.agent_journal import write_journal


def workspace_status():
    return {
        "time": time.time(),
        "mode": "safe_autonomous_workspace_v1",
        "can_plan": True,
        "can_execute_safe_tasks": True,
        "approval_required_for": ["checkpoint", "deploy_vercel_test_app", "tap", "swipe", "payments", "messages"],
        "missions": mission_status(),
    }


def plan_from_prompt(prompt):
    text = (prompt or "").lower()
    tasks = []

    if any(w in text for w in ["ui", "dashboard", "interface", "κουμπ", "μενού"]):
        tasks = [
            {"title": "Check current code health", "action": "code_health"},
            {"title": "Check git status", "action": "git_status"},
            {"title": "Run reality check", "action": "reality_status"},
            {"title": "Full validation after UI planning", "action": "full_validation"},
        ]
        title = "UI improvement mission"

    elif any(w in text for w in ["android", "companion", "κινητό", "tap", "back", "home"]):
        tasks = [
            {"title": "Check companion status", "action": "companion_status"},
            {"title": "Request UI tree", "action": "companion_ui_tree"},
            {"title": "Run reality check", "action": "reality_status"},
        ]
        title = "Android companion mission"

    elif any(w in text for w in ["deploy", "vercel", "ανέβασε", "internet", "site"]):
        tasks = [
            {"title": "Check Vercel status", "action": "vercel_status"},
            {"title": "Check git status", "action": "git_status"},
            {"title": "Deploy test app", "action": "deploy_vercel_test_app"},
        ]
        title = "Deployment mission"

    else:
        tasks = [
            {"title": "Check code health", "action": "code_health"},
            {"title": "Check git status", "action": "git_status"},
            {"title": "Run reality status", "action": "reality_status"},
            {"title": "Full validation", "action": "full_validation"},
        ]
        title = "General system mission"

    return {
        "title": title,
        "description": prompt,
        "tasks": tasks,
        "time": time.time(),
    }


def create_workspace_mission(prompt):
    plan = plan_from_prompt(prompt)
    mission = create_mission(plan["title"], plan["description"], plan["tasks"])
    output = {
        "ok": True,
        "plan": plan,
        "mission": mission,
        "time": time.time(),
    }
    write_journal("workspace_mission_created", output)
    return output


def run_workspace_mission(mission_id, max_steps=3):
    result = run_mission_cycle(mission_id, max_steps)
    write_journal("workspace_mission_run", result)
    return result
