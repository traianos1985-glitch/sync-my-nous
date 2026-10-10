"""Persistent mission execution with atomic task claims and truthful outcomes."""
import fcntl
import json
import os
import tempfile
import time
import uuid
from contextlib import contextmanager

from executor.ops_console import run_ops_action
from executor.agent_journal import write_journal
from executor.learning_memory import record_lesson

FILE = "data/missions.json"

SAFE_TASK_ACTIONS = {
    "git_status",
    "code_health",
    "reality_status",
    "vercel_status",
    "companion_status",
    "companion_home",
    "companion_back",
    "companion_ui_tree",
    "full_validation",
}

APPROVAL_REQUIRED = {
    "checkpoint",
    "deploy_vercel_test_app",
}


@contextmanager
def _locked_items():
    directory = os.path.dirname(FILE) or "."
    os.makedirs(directory, exist_ok=True)
    # Lock a stable sidecar because the JSON file is atomically replaced.
    with open(FILE + ".lock", "a", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)


def _load_unlocked():
    if not os.path.exists(FILE):
        return []
    try:
        with open(FILE, "r", encoding="utf-8") as handle:
            items = json.load(handle)
    except (OSError, ValueError, TypeError):
        return []
    return items if isinstance(items, list) else []


def _save_unlocked(items):
    directory = os.path.dirname(FILE) or "."
    os.makedirs(directory, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=".missions.", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(items, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, FILE)
    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


@contextmanager
def _edit_missions():
    with _locked_items():
        items = _load_unlocked()
        yield items
        _save_unlocked(items)


def _load():
    with _locked_items():
        return _load_unlocked()


def _save(items):
    with _locked_items():
        _save_unlocked(items)


def list_missions():
    return _load()


def mission_status():
    items = _load()
    valid = [mission for mission in items if isinstance(mission, dict)]
    return {
        "time": time.time(),
        "total": len(valid),
        "active": len([m for m in valid if m.get("status") == "active"]),
        "done": len([m for m in valid if m.get("status") == "done"]),
        "blocked": len([m for m in valid if m.get("status") == "blocked"]),
        "missions": valid[-20:],
    }


def create_mission(title, description="", tasks=None):
    if not isinstance(title, str) or not title.strip():
        return {"ok": False, "error": "mission_title_required"}
    if tasks is None:
        tasks = []
    if not isinstance(tasks, list) or any(not isinstance(task, dict) for task in tasks):
        return {"ok": False, "error": "tasks_must_be_a_list_of_objects"}

    now = time.time()
    mission = {
        "id": int(time.time_ns()),
        "title": title.strip(),
        "description": str(description),
        "status": "active",
        "created": now,
        "updated": now,
        "tasks": [],
        "approvals": [],
        "result": None,
    }

    for task in tasks:
        task_id = int(time.time_ns()) + len(mission["tasks"])
        mission["tasks"].append({
            "id": task_id,
            "title": str(task.get("title", task.get("action", "task"))),
            "action": task.get("action"),
            "payload": task.get("payload", {}) if isinstance(task.get("payload", {}), dict) else {},
            "status": "pending",
            "created": time.time(),
            "started": None,
            "finished": None,
            "result": None,
            "requires_approval": task.get("action") in APPROVAL_REQUIRED,
            "approved": False,
        })

    with _edit_missions() as items:
        existing_ids = {str(item.get("id")) for item in items if isinstance(item, dict)}
        while str(mission["id"]) in existing_ids:
            mission["id"] += 1
        items.append(mission)
    write_journal("mission_created", {"id": mission["id"], "title": mission["title"], "task_count": len(mission["tasks"])})
    return mission


def create_standard_mission(kind):
    if kind == "system_check":
        return create_mission(
            "System health and reality check",
            "Run safe checks across code, git, reality gate, companion and deploy state.",
            [
                {"title": "Check code health", "action": "code_health"},
                {"title": "Check git status", "action": "git_status"},
                {"title": "Check reality gate", "action": "reality_status"},
                {"title": "Check companion", "action": "companion_status"},
                {"title": "Full validation", "action": "full_validation"},
            ],
        )
    if kind == "android_check":
        return create_mission(
            "Android companion check",
            "Verify companion bridge actions.",
            [
                {"title": "Companion status", "action": "companion_status"},
                {"title": "Request UI tree", "action": "companion_ui_tree"},
            ],
        )
    if kind == "deploy_check":
        return create_mission(
            "Deploy verification",
            "Check deploy backend and optionally deploy test app.",
            [
                {"title": "Vercel status", "action": "vercel_status"},
                {"title": "Deploy test app", "action": "deploy_vercel_test_app"},
            ],
        )
    return {"ok": False, "error": "unknown_standard_mission", "available": ["system_check", "android_check", "deploy_check"]}


def _find_mission(items, mission_id):
    for mission in items:
        if isinstance(mission, dict) and str(mission.get("id")) == str(mission_id):
            return mission
    return None


def approve_task(mission_id, task_id):
    with _edit_missions() as items:
        mission = _find_mission(items, mission_id)
        if not mission:
            return {"ok": False, "error": "mission_not_found"}
        for task in mission.get("tasks", []):
            if str(task.get("id")) == str(task_id):
                if task.get("status") not in {"pending", "waiting_approval"}:
                    return {"ok": False, "error": "task_not_awaiting_approval", "status": task.get("status")}
                task["approved"] = True
                task["status"] = "pending"
                mission["updated"] = time.time()
                return {"ok": True, "mission": mission, "task": task}
        return {"ok": False, "error": "task_not_found"}


def reject_task(mission_id, task_id):
    """Reject a task awaiting operator approval."""
    with _edit_missions() as items:
        mission = _find_mission(items, mission_id)
        if not mission:
            return {"ok": False, "error": "mission_not_found"}
        for task in mission.get("tasks", []):
            if str(task.get("id")) == str(task_id):
                if task.get("status") not in {"pending", "waiting_approval"}:
                    return {"ok": False, "error": "task_not_awaiting_decision", "status": task.get("status")}
                task["approved"] = False
                task["status"] = "rejected"
                mission["updated"] = time.time()
                return {"ok": True, "mission": mission, "task": task}
        return {"ok": False, "error": "task_not_found"}


def run_next_mission_task(mission_id):
    # Claim the task while holding the state lock, then release the lock before
    # calling external operations. A second worker will see "running", not pending.
    with _edit_missions() as items:
        mission = _find_mission(items, mission_id)
        if not mission:
            return {"ok": False, "error": "mission_not_found"}
        if mission.get("status") not in {"active", "blocked"}:
            return {"ok": False, "error": "mission_not_active", "mission": mission}

        tasks = mission.get("tasks", [])
        pending = [task for task in tasks if task.get("status") == "pending"]
        if not pending:
            if tasks and all(task.get("status") == "done" for task in tasks):
                mission["status"] = "done"
                mission["result"] = "all_tasks_done"
            mission["updated"] = time.time()
            return {"ok": True, "idle": True, "mission": mission}

        task = pending[0]
        action = task.get("action")
        if action in APPROVAL_REQUIRED and not task.get("approved"):
            task["status"] = "waiting_approval"
            mission["status"] = "blocked"
            mission["updated"] = time.time()
            return {"ok": False, "approval_required": True, "mission": mission, "task": task}

        if action not in SAFE_TASK_ACTIONS and action not in APPROVAL_REQUIRED:
            task["status"] = "blocked"
            task["result"] = {"error": "action_not_allowed_in_mission", "action": action}
            mission["status"] = "blocked"
            mission["updated"] = time.time()
            return {"ok": False, "blocked": True, "mission": mission, "task": task}

        claim_id = uuid.uuid4().hex
        task["status"] = "running"
        task["started"] = time.time()
        task["execution_id"] = claim_id
        mission["updated"] = time.time()
        claimed_action = action
        claimed_payload = task.get("payload", {})
        claimed_task_id = task.get("id")

    try:
        result = run_ops_action(claimed_action, claimed_payload)
        if not isinstance(result, dict):
            result = {"ok": False, "error": "malformed_action_result", "result_type": type(result).__name__}
    except Exception as exc:
        result = {"ok": False, "error": "action_execution_exception", "detail": str(exc)[:1000]}

    execution_ok = result.get("ok") is True
    with _edit_missions() as items:
        mission = _find_mission(items, mission_id)
        if not mission:
            return {"ok": False, "error": "mission_disappeared_after_execution", "execution_ok": False, "result": result}
        task = next(
            (item for item in mission.get("tasks", [])
             if str(item.get("id")) == str(claimed_task_id)
             and item.get("execution_id") == claim_id
             and item.get("status") == "running"),
            None,
        )
        if task is None:
            return {"ok": False, "error": "task_claim_lost_after_execution", "execution_ok": False, "result": result}

        task["finished"] = time.time()
        task["result"] = result
        task["status"] = "done" if execution_ok else "failed"
        task["execution_ok"] = execution_ok
        if not execution_ok:
            mission["status"] = "blocked"
            mission["result"] = "task_execution_failed"
        elif mission.get("tasks") and all(item.get("status") == "done" for item in mission["tasks"]):
            mission["status"] = "done"
            mission["result"] = "all_tasks_done"
        else:
            mission["status"] = "active"
        mission["updated"] = time.time()
        output = {
            "ok": execution_ok,
            "execution_ok": execution_ok,
            "mission": mission,
            "task": task,
        }

    try:
        record_lesson(
            lesson=f"Mission task {'completed' if execution_ok else 'failed'}: {task.get('title')}",
            outcome="success" if execution_ok else "failure",
            mission_id=mission.get("id"),
            confidence=0.8,
            tags=["mission", claimed_action or "unknown"],
        )
    except Exception:
        pass

    write_journal("mission_task_run", {
        "mission_id": mission.get("id"),
        "task_id": claimed_task_id,
        "execution_id": claim_id,
        "execution_ok": execution_ok,
        "result": result,
    })
    return output


def run_mission_cycle(mission_id, max_steps=3):
    try:
        step_limit = max(1, min(int(max_steps), 25))
    except (TypeError, ValueError, OverflowError):
        step_limit = 3
    results = []
    for _ in range(step_limit):
        result = run_next_mission_task(mission_id)
        results.append(result)
        if (
            not result.get("ok")
            or result.get("idle")
            or result.get("approval_required")
            or result.get("blocked")
            or result.get("mission", {}).get("status") in {"done", "blocked"}
        ):
            break
    successful = all(result.get("ok") or result.get("idle") for result in results)
    return {
        "ok": successful,
        "status": "completed" if successful else "failed_or_blocked",
        "results": results,
        "time": time.time(),
    }


def pending_approvals():
    items = _load()
    approvals = []
    for mission in items:
        if not isinstance(mission, dict):
            continue
        for task in mission.get("tasks", []):
            if task.get("status") == "waiting_approval" or (
                task.get("requires_approval")
                and not task.get("approved")
                and task.get("status") in ["pending", "waiting_approval"]
            ):
                approvals.append({
                    "mission_id": mission.get("id"),
                    "mission_title": mission.get("title"),
                    "task_id": task.get("id"),
                    "task_title": task.get("title"),
                    "action": task.get("action"),
                    "status": task.get("status"),
                    "approved": task.get("approved"),
                    "created": task.get("created"),
                })
    return {"time": time.time(), "count": len(approvals), "approvals": approvals}
