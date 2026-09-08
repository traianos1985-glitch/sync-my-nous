import time

from executor.personal_agent import load_db
from executor.task_queue import add_task, next_task, update_task, list_queue
from executor.memory import save
from executor.project_progress import project_summary
from executor.progress_linker import link_task_to_project


def seed_goals_to_queue():
    db = load_db()
    created = []

    for goal in db.get("goals", []):
        title = goal.get("goal") if isinstance(goal, dict) else str(goal)
        if not title:
            continue

        existing = [
            x for x in list_queue()
            if x.get("kind") == "goal" and x.get("payload", {}).get("goal") == title
        ]

        if existing:
            continue

        created.append(add_task(
            title=f"Δούλεψε στόχο: {title}",
            kind="goal",
            priority=3,
            payload={"goal": title}
        ))

    return created


def execute_task(item):
    kind = item.get("kind")
    title = item.get("title")

    if kind == "goal":
        goal = item.get("payload", {}).get("goal", title)
        return {
            "summary": f"Ο στόχος '{goal}' είναι ενεργός.",
            "next_step": "Σύνδεσε τον στόχο με το πιο σχετικό project step.",
            "status": "reviewed",
            "projects_progress": project_summary(),
        }

    return {
        "summary": f"Ελέγχθηκε εργασία: {title}",
        "status": "reviewed",
    }


def run_next_task():
    item = next_task()
    if not item:
        return {"idle": True, "reason": "no_pending_tasks"}

    update_task(
        item["id"],
        status="running",
        started=time.time(),
        attempts=int(item.get("attempts", 0)) + 1,
    )

    try:
        result = execute_task(item)
        updated = update_task(
            item["id"],
            status="done",
            finished=time.time(),
            result=result,
            last_error=None,
        )
        project_link = link_task_to_project(updated)
        save({"event": "goal_executor_task_done", "task": updated, "project_link": project_link})
        return {"ok": True, "task": updated, "project_link": project_link}
    except Exception as e:
        updated = update_task(
            item["id"],
            status="failed",
            finished=time.time(),
            last_error=str(e),
        )
        save({"event": "goal_executor_task_failed", "task": updated})
        return {"ok": False, "error": str(e), "task": updated}


def goal_executor_cycle():
    seeded = seed_goals_to_queue()
    ran = run_next_task()
    return {
        "seeded": seeded,
        "ran": ran,
        "queue": list_queue(),
    }
