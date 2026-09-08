import json
import os
import time

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


def list_missions():
    return _load()


def mission_status():
    items = _load()
    return {
        "time": time.time(),
        "total": len(items),
        "active": len([m for m in items if m.get("status") == "active"]),
        "done": len([m for m in items if m.get("status") == "done"]),
        "blocked": len([m for m in items if m.get("status") == "blocked"]),
        "missions": items[-20:],
    }


def create_mission(title, description="", tasks=None):
    tasks = tasks or []
    mission = {
        "id": int(time.time_ns()),
        "title": title,
        "description": description,
        "status": "active",
        "created": time.time(),
        "updated": time.time(),
        "tasks": [],
        "approvals": [],
        "result": None,
    }

    for task in tasks:
        mission["tasks"].append({
            "id": int(time.time_ns()) + len(mission["tasks"]),
            "title": task.get("title", task.get("action", "task")),
            "action": task.get("action"),
            "payload": task.get("payload", {}),
            "status": "pending",
            "created": time.time(),
            "started": None,
            "finished": None,
            "result": None,
            "requires_approval": task.get("action") in APPROVAL_REQUIRED,
            "approved": False,
        })

    items = _load()
    items.append(mission)
    _save(items)
    write_journal("mission_created", mission)
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
    for m in items:
        if str(m.get("id")) == str(mission_id):
            return m
    return None


def approve_task(mission_id, task_id):
    items = _load()
    m = _find_mission(items, mission_id)
    if not m:
        return {"ok": False, "error": "mission_not_found"}

    for t in m.get("tasks", []):
        if str(t.get("id")) == str(task_id):
            t["approved"] = True
            t["status"] = "pending"
            m["updated"] = time.time()
            _save(items)
            return {"ok": True, "mission": m, "task": t}

    return {"ok": False, "error": "task_not_found"}


def run_next_mission_task(mission_id):
    items = _load()
    m = _find_mission(items, mission_id)
    if not m:
        return {"ok": False, "error": "mission_not_found"}

    if m.get("status") not in ["active", "blocked"]:
        return {"ok": False, "error": "mission_not_active", "mission": m}

    pending = [t for t in m.get("tasks", []) if t.get("status") == "pending"]
    if not pending:
        if all(t.get("status") == "done" for t in m.get("tasks", [])):
            m["status"] = "done"
            m["result"] = "all_tasks_done"
        m["updated"] = time.time()
        _save(items)
        return {"ok": True, "idle": True, "mission": m}

    task = pending[0]
    action = task.get("action")

    if action in APPROVAL_REQUIRED and not task.get("approved"):
        task["status"] = "waiting_approval"
        m["status"] = "blocked"
        m["updated"] = time.time()
        _save(items)
        return {"ok": False, "approval_required": True, "mission": m, "task": task}

    if action not in SAFE_TASK_ACTIONS and action not in APPROVAL_REQUIRED:
        task["status"] = "blocked"
        task["result"] = {"error": "action_not_allowed_in_mission", "action": action}
        m["status"] = "blocked"
        m["updated"] = time.time()
        _save(items)
        return {"ok": False, "blocked": True, "mission": m, "task": task}

    task["status"] = "running"
    task["started"] = time.time()
    _save(items)

    result = run_ops_action(action, task.get("payload", {}))

    task["finished"] = time.time()
    task["result"] = result
    task["status"] = "done" if result.get("ok") else "failed"

    if task["status"] == "failed":
        m["status"] = "blocked"
    elif all(t.get("status") == "done" for t in m.get("tasks", [])):
        m["status"] = "done"
        m["result"] = "all_tasks_done"
    else:
        m["status"] = "active"

    m["updated"] = time.time()
    _save(items)

    output = {"ok": True, "mission": m, "task": task}

    try:
        record_lesson(
            lesson=f"Mission task completed: {task.get('title')}",
            outcome="success" if task.get("status") == "done" else "failure",
            mission_id=m.get("id"),
            confidence=0.8,
            tags=["mission", task.get("action", "unknown")]
        )
    except Exception:
        pass

    write_journal("mission_task_run", output)
    return output


def run_mission_cycle(mission_id, max_steps=3):
    results = []
    for _ in range(int(max_steps)):
        r = run_next_mission_task(mission_id)
        results.append(r)
        if not r.get("ok") or r.get("idle") or r.get("mission", {}).get("status") in ["done", "blocked"]:
            break
    return {
        "ok": True,
        "results": results,
        "time": time.time(),
    }


def pending_approvals():
    items = _load()
    approvals = []

    for mission in items:
        for task in mission.get("tasks", []):
            if task.get("status") == "waiting_approval" or (
                task.get("requires_approval") and not task.get("approved") and task.get("status") in ["pending", "waiting_approval"]
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

    return {
        "time": time.time(),
        "count": len(approvals),
        "approvals": approvals,
    }
