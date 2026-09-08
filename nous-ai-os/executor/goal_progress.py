import json
import os
import time

from executor.personal_agent import load_db
from executor.project_progress import project_summary
from executor.memory import save

FILE = "data/goal_progress.json"


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


def sync_goals():
    db = load_db()
    items = _load()
    existing = {x.get("goal") for x in items}
    created = []

    for goal in db.get("goals", []):
        title = goal.get("goal") if isinstance(goal, dict) else str(goal)
        if not title or title in existing:
            continue

        item = {
            "id": int(time.time_ns()),
            "goal": title,
            "status": "active",
            "progress_percent": 0,
            "created": time.time(),
            "updated": time.time(),
            "last_reason": "synced_from_personal_agent",
        }
        items.append(item)
        created.append(item)

    _save(items)
    return {"created": created, "goals": items}


def list_goal_progress():
    sync_goals()
    return _load()


def estimate_goal_progress(goal_text):
    text = str(goal_text).lower()
    projects = project_summary()

    if not projects:
        return 0

    relevant = []

    for project in projects:
        name = str(project.get("project", "")).lower()
        score = 0

        if "νους" in text and "νους" in name:
            score += 3
        if "agent" in text and "agent" in name:
            score += 2
        if "mobile" in name or "κινητό" in text:
            score += 1

        if score > 0:
            relevant.append(project.get("progress_percent", 0))

    if relevant:
        return int(sum(relevant) / len(relevant))

    return 0


def refresh_goal_progress():
    items = list_goal_progress()
    changed = []

    for item in items:
        percent = estimate_goal_progress(item.get("goal", ""))
        old = int(item.get("progress_percent", 0))

        item["progress_percent"] = percent
        item["updated"] = time.time()

        if percent >= 100:
            item["status"] = "done"
            item["last_reason"] = "project_progress_complete"
        elif percent > old:
            item["status"] = "active"
            item["last_reason"] = "project_progress_increased"
        else:
            item["last_reason"] = "no_change"

        if percent != old:
            changed.append(item)

    _save(items)
    save({"event": "goal_progress_refreshed", "changed": changed})
    return {"changed": changed, "goals": items}


def goal_progress_summary():
    goals = refresh_goal_progress()["goals"]
    return {
        "total": len(goals),
        "active": len([g for g in goals if g.get("status") == "active"]),
        "done": len([g for g in goals if g.get("status") == "done"]),
        "goals": goals,
    }
