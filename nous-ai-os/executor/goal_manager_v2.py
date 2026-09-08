import json
import os
import time

FILE = "data/goal_projects_v2.json"

PROJECT_TEMPLATES = {
    "cloud": [
        {"title": "Cloud Brain Backup", "milestones": ["backup status", "backup retention", "restore preview", "cloud sync plan"]},
        {"title": "Deploy Readiness", "milestones": ["vercel status", "safe deploy approval", "deployment history"]},
    ],
    "ui": [
        {"title": "Mobile Dashboard UX", "milestones": ["command center", "pending inbox", "home badge", "button audit"]},
        {"title": "Control Center Flow", "milestones": ["approve/reject everywhere", "live output clarity", "navigation cleanup"]},
    ],
    "android": [
        {"title": "Android Companion Safe Control", "milestones": ["companion status", "ui tree", "safe intents", "tap approval gate"]},
    ],
    "autonomy": [
        {"title": "Executive Loop", "milestones": ["scheduler", "safe executor", "self diagnosis", "self healing proposals"]},
        {"title": "Code Evolution", "milestones": ["deep analyst", "patch generator", "compile audit", "approval apply"]},
    ],
}


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


def _goal_category(goal):
    t = str(goal).lower()
    if "cloud" in t or "restore" in t or "restorable" in t:
        return "cloud"
    if "interface" in t or "dashboard" in t or "ui" in t:
        return "ui"
    if "android" in t or "companion" in t:
        return "android"
    return "autonomy"


def goal_manager_status():
    items = _load()
    return {
        "time": time.time(),
        "projects": len(items),
        "active": len([x for x in items if x.get("status") == "active"]),
        "done": len([x for x in items if x.get("status") == "done"]),
        "items": items,
    }


def generate_projects_from_goals():
    from executor.goal_system import list_goals

    goals = list_goals()
    items = _load()
    existing = {(str(x.get("goal_id")), x.get("title")) for x in items}
    created = []

    for g in goals:
        category = _goal_category(g)
        for tpl in PROJECT_TEMPLATES.get(category, []):
            key = (str(g.get("id")), tpl["title"])
            if key in existing:
                continue

            project = {
                "id": int(time.time_ns()),
                "goal_id": g.get("id"),
                "goal_title": g.get("title"),
                "category": category,
                "title": tpl["title"],
                "status": "active",
                "progress": 0,
                "created": time.time(),
                "updated": time.time(),
                "milestones": [
                    {
                        "id": int(time.time_ns()) + i,
                        "title": m,
                        "status": "pending",
                        "created": time.time(),
                        "updated": None,
                    }
                    for i, m in enumerate(tpl["milestones"])
                ],
            }
            items.append(project)
            created.append(project)

    _save(items)
    return {"ok": True, "created": created, "count": len(created), "status": goal_manager_status()}


def update_project_progress():
    items = _load()
    changed = []

    for p in items:
        milestones = p.get("milestones", [])
        if not milestones:
            continue
        done = len([m for m in milestones if m.get("status") == "done"])
        new_progress = int((done / len(milestones)) * 100)
        if new_progress != int(p.get("progress", 0)):
            old = p.get("progress", 0)
            p["progress"] = new_progress
            p["updated"] = time.time()
            if new_progress >= 100:
                p["status"] = "done"
            changed.append({"project_id": p.get("id"), "title": p.get("title"), "old": old, "new": new_progress})

    _save(items)
    return {"ok": True, "changed": changed, "status": goal_manager_status()}


def list_goal_projects(limit=100):
    return _load()[-int(limit):]
