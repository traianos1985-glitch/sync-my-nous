import fcntl
import json
import os
import tempfile
import time
from contextlib import contextmanager

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


@contextmanager
def _state_lock():
    os.makedirs(os.path.dirname(FILE) or ".", exist_ok=True)
    with open(FILE + ".lock", "a", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _load_unlocked():
    if not os.path.exists(FILE):
        return {"enabled": False, "runs": [], "last_run": None}
    try:
        with open(FILE, "r", encoding="utf-8") as handle:
            state = json.load(handle)
        if not isinstance(state, dict):
            raise ValueError("state_not_object")
        state.setdefault("enabled", False)
        state.setdefault("runs", [])
        state.setdefault("last_run", None)
        return state
    except (OSError, ValueError, TypeError):
        return {"enabled": False, "runs": [], "last_run": None, "error": "state_load_failed"}


def _save_unlocked(state):
    directory = os.path.dirname(FILE) or "."
    os.makedirs(directory, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=".auto_mission_executor.", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(state, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, FILE)
    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def _load():
    with _state_lock():
        return _load_unlocked()


def _save(state):
    with _state_lock():
        _save_unlocked(state)


def _task_allowed(task):
    if not isinstance(task, dict):
        return False, "invalid_task"
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
    if not isinstance(tasks, list):
        return {"safe": False, "reason": "invalid_tasks", "pending": 0, "blocked_tasks": []}
    pending = [task for task in tasks if isinstance(task, dict) and task.get("status") == "pending"]
    if not pending:
        return {"safe": False, "reason": "no_pending_tasks", "pending": 0, "blocked_tasks": []}

    blocked = []
    for task in pending:
        allowed, reason = _task_allowed(task)
        if not allowed:
            blocked.append({
                "task_id": task.get("id"),
                "title": task.get("title"),
                "action": task.get("action"),
                "reason": reason,
            })
    return {
        "safe": not blocked,
        "reason": "safe" if not blocked else "blocked_tasks",
        "pending": len(pending),
        "blocked_tasks": blocked,
    }


def auto_mission_executor_status():
    state = _load()
    ms = mission_status()
    candidates = []
    blocked = []
    for mission in ms.get("missions", []):
        if not isinstance(mission, dict) or mission.get("status") != "active":
            continue
        summary = _mission_safe_summary(mission)
        item = {
            "mission_id": mission.get("id"),
            "title": mission.get("title"),
            "status": mission.get("status"),
            "safe": summary.get("safe"),
            "reason": summary.get("reason"),
            "pending": summary.get("pending"),
            "blocked_tasks": summary.get("blocked_tasks"),
        }
        (candidates if summary.get("safe") else blocked).append(item)
    return {
        "time": time.time(),
        "enabled": state.get("enabled", False),
        "safe_actions": sorted(SAFE_AUTO_ACTIONS),
        "blocked_actions": sorted(BLOCKED_AUTO_ACTIONS),
        "run_in_progress": state.get("run_in_progress"),
        "candidates": candidates,
        "blocked": blocked,
        "last_run": state.get("last_run"),
        "recent_runs": state.get("runs", [])[-10:],
    }


def set_auto_mission_executor_enabled(enabled):
    with _state_lock():
        state = _load_unlocked()
        state["enabled"] = bool(enabled)
        _save_unlocked(state)
    return {"ok": True, "enabled": bool(enabled), "status": auto_mission_executor_status()}


def run_auto_mission_executor(max_missions=1, max_steps_per_mission=3, trigger="manual"):
    try:
        mission_limit = max(1, min(int(max_missions), 10))
    except (TypeError, ValueError, OverflowError):
        mission_limit = 1
    try:
        step_limit = max(1, min(int(max_steps_per_mission), 25))
    except (TypeError, ValueError, OverflowError):
        step_limit = 3

    # Durable single-run claim: concurrent scheduler ticks cannot execute the
    # same candidate missions at the same time. The lock is not held in actions.
    with _state_lock():
        state = _load_unlocked()
        if state.get("run_in_progress"):
            return {"ok": False, "error": "run_already_in_progress"}
        run_id = str(time.time_ns())
        state["run_in_progress"] = {"id": run_id, "started": time.time(), "trigger": str(trigger)}
        _save_unlocked(state)

    run = {
        "id": run_id,
        "time": time.time(),
        "trigger": str(trigger),
        "max_missions": mission_limit,
        "max_steps_per_mission": step_limit,
        "executed": [],
        "skipped": [],
        "post_checks": {},
    }
    try:
        status = auto_mission_executor_status()
        candidates = status.get("candidates", [])[:mission_limit]
        for candidate in candidates:
            mission_id = candidate.get("mission_id")
            try:
                result = run_mission_cycle(mission_id, step_limit)
            except Exception as exc:
                result = {"ok": False, "status": "executor_exception", "error": str(exc)[:1000], "results": []}
            run["executed"].append({
                "mission_id": mission_id,
                "title": candidate.get("title"),
                "result": result,
                "ok": result.get("ok") is True,
            })
        run["skipped"] = status.get("blocked", [])

        try:
            run["post_checks"]["goal_progress"] = apply_goal_progress_intelligence()
        except Exception as exc:
            run["post_checks"]["goal_progress_error"] = str(exc)[:1000]
        try:
            run["post_checks"]["self_diagnosis"] = run_self_diagnosis()
        except Exception as exc:
            run["post_checks"]["self_diagnosis_error"] = str(exc)[:1000]

        executed_ok = bool(run["executed"]) and all(item["ok"] for item in run["executed"])
        if executed_ok and not run["skipped"]:
            run["status"] = "completed"
        elif run["executed"] and executed_ok:
            run["status"] = "partial"
        elif run["executed"]:
            run["status"] = "failed"
        else:
            run["status"] = "no_work"

        record_decision(
            title="Auto mission executor run",
            reason="Executed only safe allowlisted mission tasks.",
            action="auto_mission_executor",
            result={
                "trigger": trigger,
                "status": run["status"],
                "executed_count": len(run["executed"]),
                "skipped_count": len(run["skipped"]),
            },
            confidence=0.8,
            tags=["auto_executor", "safe_mode", str(trigger)],
        )
        record_lesson(
            lesson="Auto mission executor run ended with status %s (%s executed, %s skipped)."
            % (run["status"], len(run["executed"]), len(run["skipped"])),
            outcome="success" if run["status"] == "completed" else "failure",
            confidence=0.75,
            tags=["auto_executor", "safe_mode", str(trigger)],
        )
        with _state_lock():
            state = _load_unlocked()
            state["last_run"] = run
            state.setdefault("runs", []).append(run)
            state["runs"] = state["runs"][-50:]
            state.pop("run_in_progress", None)
            _save_unlocked(state)
        return {"ok": run["status"] == "completed", "run": run, "status": auto_mission_executor_status()}
    except Exception:
        with _state_lock():
            state = _load_unlocked()
            state.pop("run_in_progress", None)
            _save_unlocked(state)
        raise
