import time

from executor.project_progress import list_progress
from executor.memory import save


def _save_projects(projects):
    import json, os
    os.makedirs("data", exist_ok=True)
    json.dump(projects, open("data/project_progress.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def find_best_project_for_task(task, projects=None):
    if projects is None:
        projects = list_progress()
    text = (str(task.get("title", "")) + " " + str(task.get("payload", {}))).lower()

    best = None
    best_score = 0

    for project in projects:
        name = str(project.get("project", "")).lower()
        score = 0

        for word in name.split():
            if len(word) > 2 and word in text:
                score += 1

        if "νους" in text and "νους" in name:
            score += 3
        if "agent" in text and "agent" in name:
            score += 2

        if score > best_score:
            best = project
            best_score = score

    return best


def ensure_project_step(project, step_text):
    steps = project.get("steps", [])
    for step in steps:
        if isinstance(step, dict) and step.get("step") == step_text:
            return step

    step = {
        "step": step_text,
        "status": "suggested",
        "created": time.time(),
        "updated": time.time(),
    }
    steps.append(step)
    project["steps"] = steps
    return step


def link_task_to_project(task):
    projects = list_progress()
    project = find_best_project_for_task(task, projects)

    if not project:
        return {
            "linked": False,
            "reason": "no_matching_project",
        }

    step_text = task.get("title", "agent task")
    step = ensure_project_step(project, step_text)
    step["status"] = "done"
    step["updated"] = time.time()

    project["updated"] = time.time()

    _save_projects(projects)

    result = {
        "linked": True,
        "project": project.get("project"),
        "step": step_text,
        "status": "done",
    }

    save({"event": "task_linked_to_project", "result": result})
    return result


def progress_snapshot():
    projects = list_progress()
    output = []

    for project in projects:
        steps = project.get("steps", [])
        total = len(steps)
        done = len([s for s in steps if isinstance(s, dict) and s.get("status") == "done"])
        output.append({
            "project": project.get("project"),
            "total": total,
            "done": done,
            "percent": int((done / total) * 100) if total else 0,
        })

    return output
