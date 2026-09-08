import json
import os
import time

from executor.mission_system import mission_status, run_mission_cycle
from executor.goal_progress_intelligence import apply_goal_progress_intelligence
from executor.learning_memory import record_lesson
from executor.decision_memory import record_decision
from executor.self_diagnosis import run_self_diagnosis

FILE = "data/auto_mission_executor.json"

SAFE_AUTO_ACTIONS = {
    "code_health",
    "git_status",
    "full_validation",
    "reality_status",
    "companion_status",
    "companion_ui_tree",
    "vercel_status",
}

BLOCKED_AUTO_ACTIONS = {
    "deploy_vercel_test_app",
    "checkpoint",
    "restore_brain_backup",
    "delete_files",
    "git_commit",
    "git_push",
    "android_tap",
    "tap",
}


def _load():
    if not os.path.exists(FILE):
        return {
            "enabled": False,
            "runs": [],
            "last_run": None,
        }
    try:
        return json.load(open(FILE, "r", encoding="utf-8"))
    except Exception:
        return {
            "enabled": False,
            "runs": [],
            "last_run": None,
            "error": "state_load_failed",
        }


def _save(state):
    os.makedirs("data", exist_ok=True)
    json.dump(state, open(FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def _task_allowed(task):
    action = task.get("action")
    if action in BLOCKED_AUTO_ACTIONS:
        return False, "blocked_action"
    if task.get("requires_approval") and not task.get("approved"):
        return False, "requires_approval"
    if action not in SAFE_AUTO_ACTIONS:
        return False, "not_in_safe_allowlist"
    return True, "safe"


def _mission_safe_summary(mission):
    tasks = mission.get("tasks", [])
    pending = [t for t in tasks if t.get("status") == "pending"]

    if not pending:
        return {
            "safe": False,
            "reason": "no_pending_tasks",
            "pending": 0,
            "blocked_tasks": [],
        }

    blocked = []
    for t in pending:
        allowed, reason = _task_allowed(t)
        if not allowed:
            blocked.append({
                "task_id": t.get("id"),
                "title": t.get("title"),
                "action": t.get("action"),
                "reason": reason,
            })

    return {
        "safe": len(blocked) == 0,
        "reason": "safe" if len(blocked) == 0 else "blocked_tasks",
        "pending": len(pending),
        "blocked_tasks": blocked,
    }


def auto_mission_executor_status():
    state = _load()
    ms = mission_status()

    candidates = []
    blocked = []

    for m in ms.get("missions", []):
        if m.get("status") not in ["active"]:
            continue

        summary = _mission_safe_summary(m)
        item = {
            "mission_id": m.get("id"),
            "title": m.get("title"),
            "status": m.get("status"),
            "safe": summary.get("safe"),
            "reason": summary.get("reason"),
            "pending": summary.get("pending"),
            "blocked_tasks": summary.get("blocked_tasks"),
        }

        if summary.get("safe"):
            candidates.append(item)
        else:
            blocked.append(item)

    return {
        "time": time.time(),
        "enabled": state.get("enabled", False),
        "safe_actions": sorted(list(SAFE_AUTO_ACTIONS)),
        "blocked_actions": sorted(list(BLOCKED_AUTO_ACTIONS)),
        "candidates": candidates,
        "blocked": blocked,
        "last_run": state.get("last_run"),
        "recent_runs": state.get("runs", [])[-10:],
    }


def set_auto_mission_executor_enabled(enabled):
    state = _load()
    state["enabled"] = bool(enabled)
    _save(state)
    return {"ok": True, "enabled": state["enabled"], "status": auto_mission_executor_status()}


def run_auto_mission_executor(max_missions=1, max_steps_per_mission=3, trigger="manual"):
    state = _load()
    status = auto_mission_executor_status()

    run = {
        "id": int(time.time_ns()),
        "time": time.time(),
        "trigger": trigger,
        "max_missions": int(max_missions),
        "max_steps_per_mission": int(max_steps_per_mission),
        "executed": [],
        "skipped": [],
        "post_checks": {},
    }

    candidates = status.get("candidates", [])[:int(max_missions)]

    for c in candidates:
        mission_id = c.get("mission_id")
        result = run_mission_cycle(mission_id, int(max_steps_per_mission))

        run["executed"].append({
            "mission_id": mission_id,
            "title": c.get("title"),
            "result": result,
        })

    for b in status.get("blocked", []):
        run["skipped"].append(b)

    try:
        run["post_checks"]["goal_progress"] = apply_goal_progress_intelligence()
    except Exception as e:
        run["post_checks"]["goal_progress_error"] = str(e)

    try:
        run["post_checks"]["self_diagnosis"] = run_self_diagnosis()
    except Exception as e:
        run["post_checks"]["self_diagnosis_error"] = str(e)

    record_decision(
        title="Auto mission executor run",
        reason="Executed only safe allowlisted mission tasks.",
        action="auto_mission_executor",
        result={
            "trigger": trigger,
            "executed_count": len(run["executed"]),
            "skipped_count": len(run["skipped"]),
        },
        confidence=0.8,
        tags=["auto_executor", "safe_mode", trigger],
    )

    record_lesson(
        lesson="Auto mission executor completed safe run with %s executed missions and %s skipped missions."
        % (len(run["executed"]), len(run["skipped"])),
        outcome="success",
        confidence=0.75,
        tags=["auto_executor", "safe_mode", trigger],
    )

    state["last_run"] = run
    state.setdefault("runs", []).append(run)
    state["runs"] = state["runs"][-50:]
    _save(state)

    return {
        "ok": True,
        "run": run,
        "status": auto_mission_executor_status(),
    }
