import time

from executor.personal_agent import load_db
from executor.task_queue import list_queue
from executor.project_progress import project_summary
from executor.scheduler_agent import list_schedules
from executor.battery_guard import battery_guard
from executor.curiosity_agent import knowledge_status
from executor.goal_progress import goal_progress_summary
from executor.agent_journal import write_journal


def score_goal(goal):
    text = goal.get("goal") if isinstance(goal, dict) else str(goal)
    score = 5

    lowered = text.lower()
    if "νους" in lowered or "agent" in lowered:
        score -= 2
    if "κινητό" in lowered or "android" in lowered:
        score -= 1

    return max(score, 1)


def prioritize_goals():
    db = load_db()
    goals = []

    for goal in db.get("goals", []):
        title = goal.get("goal") if isinstance(goal, dict) else str(goal)
        goals.append({
            "goal": title,
            "priority": score_goal(goal),
            "status": goal.get("status", "active") if isinstance(goal, dict) else "active",
        })

    goals = sorted(goals, key=lambda x: x["priority"])
    return goals


def decide_next_action():
    battery = battery_guard()
    queue = list_queue()
    pending = [x for x in queue if x.get("status") == "pending"]
    failed = [x for x in queue if x.get("status") == "failed"]
    goals = prioritize_goals()
    projects = project_summary()
    schedules = list_schedules()
    knowledge = knowledge_status()
    goal_progress = goal_progress_summary()

    if int(battery.get("level") or 100) < 25 and str(battery.get("plugged", "")).upper() == "UNPLUGGED":
        decision = {
            "action": "pause",
            "reason": "low_battery",
            "priority": 1,
            "battery": battery,
        }
    elif failed:
        decision = {
            "action": "recover_failed_tasks",
            "reason": "failed_tasks_exist",
            "priority": 2,
            "count": len(failed),
        }
    elif pending:
        decision = {
            "action": "run_next_queue_task",
            "reason": "pending_queue_task",
            "priority": 3,
            "task_id": pending[0].get("id"),
            "task": pending[0].get("title"),
        }
    elif goals:
        decision = {
            "action": "seed_goal_task",
            "reason": "active_goal_available",
            "priority": 4,
            "goal": goals[0],
        }
    elif knowledge.get("open", 0) > 0:
        decision = {
            "action": "learning_cycle",
            "reason": "open_learning_topics",
            "priority": 5,
            "open": knowledge.get("open"),
        }
    else:
        decision = {
            "action": "idle",
            "reason": "nothing_urgent",
            "priority": 9,
        }

    decision["context"] = {
        "battery": battery,
        "pending_queue": len(pending),
        "failed_queue": len(failed),
        "goals": goals[:5],
        "projects": projects,
        "schedules": len(schedules),
        "knowledge": knowledge,
        "goal_progress": goal_progress,
        "time": time.time(),
    }

    write_journal("decision_made", decision)
    return decision
