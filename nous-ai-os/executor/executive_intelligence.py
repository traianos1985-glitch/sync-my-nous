import time

from executor.goal_system import goal_status
from executor.mission_system import mission_status, pending_approvals
from executor.decision_memory import decision_status
from executor.learning_memory import lesson_status
from executor.brain_state import brain_status


def executive_intelligence_status():
    goals = goal_status()
    missions = mission_status()
    approvals = pending_approvals()
    decisions = decision_status()
    lessons = lesson_status()
    brain = brain_status()

    recommendations = []

    if approvals.get("count", 0) > 0:
        first = approvals["approvals"][0]
        recommendations.append({
            "priority": 1,
            "type": "approval",
            "title": "Resolve pending approval",
            "reason": "A mission is blocked and cannot continue until you approve or reject its task.",
            "action": "open_approvals",
            "target": first,
        })

    blocked = [m for m in missions.get("missions", []) if m.get("status") == "blocked"]
    if blocked:
        recommendations.append({
            "priority": 2,
            "type": "blocked_mission",
            "title": "Review blocked missions",
            "reason": "Blocked missions prevent goal progress and should be reviewed.",
            "action": "review_missions",
            "target": [{"id": m.get("id"), "title": m.get("title")} for m in blocked],
        })

    active_no_progress_goals = [
        g for g in goals.get("goals", [])
        if g.get("status") == "active" and int(g.get("progress", 0)) == 0
    ]
    if active_no_progress_goals:
        g = sorted(active_no_progress_goals, key=lambda x: int(x.get("priority", 3)))[0]
        recommendations.append({
            "priority": 3,
            "type": "goal_progress",
            "title": "Create or link mission to highest-priority goal",
            "reason": "A high-priority goal has no measurable progress yet.",
            "action": "open_goals",
            "target": {"id": g.get("id"), "title": g.get("title"), "priority": g.get("priority")},
        })

    if lessons.get("total", 0) < 10:
        recommendations.append({
            "priority": 4,
            "type": "learning",
            "title": "Run more safe missions to build experience",
            "reason": "The learning memory is still small. More safe missions will improve future recommendations.",
            "action": "run_safe_mission",
            "target": "system_check_or_android_check",
        })

    if brain.get("readiness", {}).get("cloud_ready_foundation") and brain.get("readiness", {}).get("device_control_foundation"):
        recommendations.append({
            "priority": 5,
            "type": "cloud_brain",
            "title": "Prepare Cloud Brain sync",
            "reason": "Brain and device foundations are ready. Backup/restore already works, so cloud sync is now realistic.",
            "action": "plan_cloud_sync",
            "target": "cloud_brain_foundation",
        })

    recommendations = sorted(recommendations, key=lambda x: x["priority"])

    return {
        "time": time.time(),
        "summary": {
            "goals_total": goals.get("total"),
            "goals_active": goals.get("active"),
            "missions_total": missions.get("total"),
            "missions_active": missions.get("active"),
            "missions_blocked": missions.get("blocked"),
            "approvals_pending": approvals.get("count"),
            "decisions_total": decisions.get("total"),
            "lessons_total": lessons.get("total"),
            "lessons_success": lessons.get("success"),
            "lessons_failure": lessons.get("failure"),
            "cloud_ready": brain.get("readiness", {}).get("cloud_ready_foundation"),
            "device_ready": brain.get("readiness", {}).get("device_control_foundation"),
        },
        "recommendations": recommendations,
        "next_best_action": recommendations[0] if recommendations else {
            "priority": 99,
            "type": "idle",
            "title": "No urgent action",
            "reason": "System appears stable.",
            "action": "monitor",
        },
    }


def executive_intelligence_report():
    status = executive_intelligence_status()
    n = status["next_best_action"]

    lines = [
        "NOUS Executive Intelligence Report",
        "",
        f"Goals: {status['summary']['goals_active']} active / {status['summary']['goals_total']} total",
        f"Missions: {status['summary']['missions_active']} active, {status['summary']['missions_blocked']} blocked",
        f"Pending approvals: {status['summary']['approvals_pending']}",
        f"Decisions: {status['summary']['decisions_total']}",
        f"Lessons: {status['summary']['lessons_total']} total, {status['summary']['lessons_success']} success, {status['summary']['lessons_failure']} failure",
        f"Cloud ready: {status['summary']['cloud_ready']}",
        f"Device ready: {status['summary']['device_ready']}",
        "",
        "Next best action:",
        f"- {n.get('title')}",
        f"- Reason: {n.get('reason')}",
        f"- Action: {n.get('action')}",
    ]

    return {
        "ok": True,
        "report": "\n".join(lines),
        "status": status,
        "time": time.time(),
    }
