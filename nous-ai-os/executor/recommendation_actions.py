import time

from executor.executive_intelligence import executive_intelligence_status
from executor.mission_system import approve_task, run_mission_cycle, create_standard_mission
from executor.goal_system import refresh_goal_progress
from executor.learning_memory import record_lesson
from executor.decision_memory import record_decision


def _get_recommendation(index):
    status = executive_intelligence_status()
    recs = status.get("recommendations", [])
    try:
        i = int(index)
    except Exception:
        i = 0

    if i < 0 or i >= len(recs):
        return None, status

    return recs[i], status


def execute_recommendation(index=0):
    rec, status = _get_recommendation(index)
    if not rec:
        return {"ok": False, "error": "recommendation_not_found", "index": index}

    action = rec.get("action")
    target = rec.get("target")
    result = None

    if action == "open_approvals":
        if isinstance(target, dict):
            result = approve_task(target.get("mission_id"), target.get("task_id"))
            if result.get("ok"):
                result["run_after_approval"] = run_mission_cycle(target.get("mission_id"), 3)
        else:
            return {"ok": False, "error": "invalid_approval_target", "recommendation": rec}

    elif action == "review_missions":
        result = {
            "ok": True,
            "message": "Review action does not auto-execute destructive work.",
            "target": target,
        }

    elif action == "open_goals":
        if isinstance(target, dict):
            result = refresh_goal_progress(target.get("id"))
        else:
            return {"ok": False, "error": "invalid_goal_target", "recommendation": rec}

    elif action == "run_safe_mission":
        mission = create_standard_mission("android_check")
        run = run_mission_cycle(mission.get("id"), 3)
        result = {"ok": True, "mission": mission, "run": run}

    elif action == "plan_cloud_sync":
        lesson = record_lesson(
            "Cloud Brain sync is recommended as next architecture step because brain/device foundations are ready.",
            outcome="success",
            confidence=0.75,
            tags=["cloud_brain", "recommendation", "planning"],
        )
        result = {"ok": True, "message": "Cloud sync planning lesson recorded.", "lesson": lesson}

    else:
        return {
            "ok": False,
            "error": "recommendation_action_not_allowed",
            "action": action,
            "recommendation": rec,
        }

    decision = record_decision(
        title="Approved recommendation: " + rec.get("title", "recommendation"),
        reason=rec.get("reason", ""),
        action=action,
        result=result,
        confidence=0.8,
        tags=["recommendation", "approved", rec.get("type", "unknown")],
    )

    return {
        "ok": True,
        "executed": True,
        "recommendation": rec,
        "result": result,
        "decision": decision,
        "time": time.time(),
    }


def reject_recommendation(index=0, reason="User rejected recommendation"):
    rec, status = _get_recommendation(index)
    if not rec:
        return {"ok": False, "error": "recommendation_not_found", "index": index}

    decision = record_decision(
        title="Rejected recommendation: " + rec.get("title", "recommendation"),
        reason=reason,
        action="reject_recommendation",
        result={"recommendation": rec},
        confidence=0.8,
        tags=["recommendation", "rejected", rec.get("type", "unknown")],
    )

    return {
        "ok": True,
        "rejected": True,
        "recommendation": rec,
        "decision": decision,
        "time": time.time(),
    }
