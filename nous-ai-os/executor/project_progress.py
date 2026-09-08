import json
import os
import time

from executor.personal_agent import load_db
from executor.memory import save

FILE = "data/project_progress.json"


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


def sync_projects():
    db = load_db()
    progress = _load()
    created = []

    existing_names = {x.get("project") for x in progress}

    for project in db.get("projects", []):
        name = project.get("project") if isinstance(project, dict) else str(project)
        if not name or name in existing_names:
            continue

        item = {
            "id": int(time.time_ns()),
            "project": name,
            "status": "active",
            "created": time.time(),
            "updated": time.time(),
            "steps": project.get("steps", []) if isinstance(project, dict) else [],
        }
        progress.append(item)
        created.append(item)

    _save(progress)
    return {"created": created, "projects": progress}


def list_progress():
    sync_projects()
    return _load()


def mark_step(project_name, step_text, status="done"):
    progress = _load()
    changed = False

    for project in progress:
        if project.get("project") != project_name:
            continue

        steps = project.get("steps", [])
        for step in steps:
            if isinstance(step, dict) and step.get("step") == step_text:
                step["status"] = status
                changed = True

        project["updated"] = time.time()

    _save(progress)
    save({"event": "project_step_updated", "project": project_name, "step": step_text, "status": status})
    return {"changed": changed, "projects": progress}


def project_summary():
    progress = list_progress()
    summary = []

    for project in progress:
        steps = project.get("steps", [])
        total = len(steps)
        done = len([s for s in steps if isinstance(s, dict) and s.get("status") == "done"])
        summary.append({
            "project": project.get("project"),
            "status": project.get("status"),
            "steps_total": total,
            "steps_done": done,
            "progress_percent": int((done / total) * 100) if total else 0,
        })

    return summary
