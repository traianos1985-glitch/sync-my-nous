import json
import os
import time

from executor.mission_system import list_missions, create_mission
from executor.agent_journal import write_journal

FILE = "data/goals_v2.json"


def _load():
    if not os.path.exists(FILE):
        return []
    try:
        return json.load(open(FILE, "r", encoding="utf-8"))
    except Exception:
        return []


def _save(items):
    os.makedirs("data", exist_ok=True)
    json.dump(items, open(FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


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


def create_goal(title, description="", priority=3):
    goal = {
        "id": int(time.time_ns()),
        "title": title,
        "description": description,
        "priority": int(priority),
        "status": "active",
        "progress": 0,
        "missions": [],
        "notes": [],
        "next_actions": [],
        "created": time.time(),
        "updated": time.time(),
    }

    items = _load()
    items.append(goal)
    _save(items)
    write_journal("goal_created", goal)
    return goal


def _find_goal(items, goal_id):
    for g in items:
        if str(g.get("id")) == str(goal_id):
            return g
    return None


def add_goal_note(goal_id, note):
    items = _load()
    g = _find_goal(items, goal_id)
    if not g:
        return {"ok": False, "error": "goal_not_found"}

    g.setdefault("notes", []).append({
        "time": time.time(),
        "note": note,
    })
    g["updated"] = time.time()
    _save(items)
    return {"ok": True, "goal": g}


def link_mission_to_goal(goal_id, mission_id):
    items = _load()
    g = _find_goal(items, goal_id)
    if not g:
        return {"ok": False, "error": "goal_not_found"}

    if str(mission_id) not in [str(x) for x in g.get("missions", [])]:
        g.setdefault("missions", []).append(mission_id)

    g["updated"] = time.time()
    _save(items)
    return {"ok": True, "goal": g}


def refresh_goal_progress(goal_id):
    items = _load()
    g = _find_goal(items, goal_id)
    if not g:
        return {"ok": False, "error": "goal_not_found"}

    missions = list_missions()
    linked = [m for m in missions if str(m.get("id")) in [str(x) for x in g.get("missions", [])]]

    if not linked:
        g["progress"] = 0
        g["next_actions"] = ["Create or link missions for this goal."]
    else:
        done = len([m for m in linked if m.get("status") == "done"])
        blocked = len([m for m in linked if m.get("status") == "blocked"])
        g["progress"] = int((done / max(len(linked), 1)) * 100)

        next_actions = []
        if blocked:
            next_actions.append("Review blocked missions and approvals.")
        if done < len(linked):
            next_actions.append("Run remaining active missions.")
        if done == len(linked):
            next_actions.append("Review results and mark goal done if satisfied.")
        g["next_actions"] = next_actions

    if g["progress"] >= 100:
        g["status"] = "done"

    g["updated"] = time.time()
    _save(items)

    return {"ok": True, "goal": g, "linked_missions": linked}


def create_goal_mission(goal_id, title, description="", tasks=None):
    mission = create_mission(title, description, tasks or [])
    link = link_mission_to_goal(goal_id, mission.get("id"))
    refresh = refresh_goal_progress(goal_id)
    return {
        "ok": True,
        "mission": mission,
        "link": link,
        "refresh": refresh,
    }


def seed_core_goals():
    items = _load()
    existing = {g.get("title") for g in items}

    seeds = [
        ("Make NOUS cloud-native and restorable", "NOUS should survive device loss and run from cloud.", 1),
        ("Improve NOUS user interface", "Make dashboard friendly, mobile-first, and agent-like.", 2),
        ("Expand Android Companion control", "Give NOUS reliable Android eyes and hands.", 1),
        ("Strengthen safe autonomy", "Missions, approvals, execution and reports.", 1),
    ]

    created = []
    for title, desc, prio in seeds:
        if title not in existing:
            created.append(create_goal(title, desc, prio))

    return {
        "created": created,
        "goals": _load(),
    }
