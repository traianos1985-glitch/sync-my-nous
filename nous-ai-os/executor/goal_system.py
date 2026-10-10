import time

from executor.json_state_store import edit_list, read_list, write_list
from executor.mission_system import list_missions, create_mission
from executor.agent_journal import write_journal

FILE = "data/goals_v2.json"


def _load():
    return read_list(FILE)


def _save(items):
    return write_list(FILE, items)


def list_goals():
    return _load()


def goal_status():
    goals = _load()
    return {
        "time": time.time(),
        "total": len(goals),
        "active": len([g for g in goals if g.get("status") == "active"]),
        "done": len([g for g in goals if g.get("status") == "done"]),
        "goals": goals[-20:],
    }


def _new_goal(title, description="", priority=3):
    now = time.time()
    return {
        "id": int(time.time_ns()),
        "title": title,
        "description": description,
        "priority": int(priority),
        "status": "active",
        "progress": 0,
        "missions": [],
        "notes": [],
        "next_actions": [],
        "created": now,
        "updated": now,
    }


def create_goal(title, description="", priority=3):
    with edit_list(FILE) as items:
        goal = _new_goal(title, description, priority)
        used = {str(item.get("id")) for item in items}
        while str(goal["id"]) in used:
            goal["id"] += 1
        items.append(goal)
    write_journal("goal_created", goal)
    return goal


def _find_goal(items, goal_id):
    for goal in items:
        if str(goal.get("id")) == str(goal_id):
            return goal
    return None


def add_goal_note(goal_id, note):
    with edit_list(FILE) as items:
        goal = _find_goal(items, goal_id)
        if not goal:
            return {"ok": False, "error": "goal_not_found"}
        goal.setdefault("notes", []).append({"time": time.time(), "note": note})
        goal["updated"] = time.time()
        result = dict(goal)
    return {"ok": True, "goal": result}


def link_mission_to_goal(goal_id, mission_id):
    with edit_list(FILE) as items:
        goal = _find_goal(items, goal_id)
        if not goal:
            return {"ok": False, "error": "goal_not_found"}
        if str(mission_id) not in [str(item) for item in goal.get("missions", [])]:
            goal.setdefault("missions", []).append(mission_id)
        goal["updated"] = time.time()
        result = dict(goal)
    return {"ok": True, "goal": result}


def refresh_goal_progress(goal_id):
    missions = list_missions()
    with edit_list(FILE) as items:
        goal = _find_goal(items, goal_id)
        if not goal:
            return {"ok": False, "error": "goal_not_found"}
        linked_ids = [str(item) for item in goal.get("missions", [])]
        linked = [mission for mission in missions if str(mission.get("id")) in linked_ids]
        if not linked:
            goal["progress"] = 0
            goal["next_actions"] = ["Create or link missions for this goal."]
        else:
            done = sum(1 for mission in linked if mission.get("status") == "done")
            blocked = sum(1 for mission in linked if mission.get("status") == "blocked")
            goal["progress"] = int((done / len(linked)) * 100)
            next_actions = []
            if blocked:
                next_actions.append("Review blocked missions and approvals.")
            if done < len(linked):
                next_actions.append("Run remaining active missions.")
            if done == len(linked):
                next_actions.append("Review results and mark goal done if satisfied.")
            goal["next_actions"] = next_actions
        if goal["progress"] >= 100:
            goal["status"] = "done"
        goal["updated"] = time.time()
        result = dict(goal)
    return {"ok": True, "goal": result, "linked_missions": linked}


def create_goal_mission(goal_id, title, description="", tasks=None):
    mission = create_mission(title, description, tasks or [])
    link = link_mission_to_goal(goal_id, mission.get("id"))
    refresh = refresh_goal_progress(goal_id)
    return {"ok": True, "mission": mission, "link": link, "refresh": refresh}


def seed_core_goals():
    seeds = [
        ("Make NOUS cloud-native and restorable", "NOUS should survive device loss and run from cloud.", 1),
        ("Improve NOUS user interface", "Make dashboard friendly, mobile-first, and agent-like.", 2),
        ("Expand Android Companion control", "Give NOUS reliable Android eyes and hands.", 1),
        ("Strengthen safe autonomy", "Missions, approvals, execution and reports.", 1),
    ]
    created = []
    with edit_list(FILE) as items:
        existing = {goal.get("title") for goal in items}
        for title, description, priority in seeds:
            if title not in existing:
                goal = _new_goal(title, description, priority)
                used = {str(item.get("id")) for item in items}
                while str(goal["id"]) in used:
                    goal["id"] += 1
                items.append(goal)
                existing.add(title)
                created.append(goal)
    for goal in created:
        write_journal("goal_created", goal)
    return {"created": created, "goals": _load()}
