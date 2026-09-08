import time

ACTIONS = [
    {"name": "dashboard", "method": "GET", "path": "/dashboard", "auth": False},
    {"name": "remote_status", "method": "GET", "path": "/remote/status", "auth": False},

    {"name": "brain_status", "method": "GET", "path": "/remote/brain/status", "auth": False},
    {"name": "backup_list", "method": "GET", "path": "/remote/brain-backup/list", "auth": False},
    {"name": "restore_status", "method": "GET", "path": "/remote/brain-restore/status", "auth": False},

    {"name": "goals_status", "method": "GET", "path": "/remote/goals-v2/status", "auth": False},
    {"name": "missions_status", "method": "GET", "path": "/remote/missions/status", "auth": False},
    {"name": "approvals", "method": "GET", "path": "/remote/missions/approvals", "auth": False},

    {"name": "lessons_status", "method": "GET", "path": "/remote/lessons/status", "auth": False},
    {"name": "decision_memory", "method": "GET", "path": "/remote/decision-memory/status", "auth": False},

    {"name": "executive_intelligence", "method": "GET", "path": "/remote/executive-intelligence/status", "auth": False},
    {"name": "scheduler_loop", "method": "GET", "path": "/remote/executive-scheduler-loop/status", "auth": False},

    {"name": "mission_planner", "method": "GET", "path": "/remote/mission-planner/status", "auth": False},
    {"name": "mission_proposals", "method": "GET", "path": "/remote/mission-planner/proposals", "auth": False},

    {"name": "goal_progress_intelligence", "method": "GET", "path": "/remote/goal-progress-intelligence/status", "auth": False},

    {"name": "protected_planner_propose", "method": "POST", "path": "/remote/mission-planner/propose", "auth": True},
    {"name": "protected_scheduler_run_once", "method": "POST", "path": "/remote/executive-scheduler-loop/run-once", "auth": True},
    {"name": "protected_backup_create", "method": "POST", "path": "/remote/brain-backup/create", "auth": True},
]


def dashboard_action_audit(app, token=""):
    client = app.test_client()
    results = []

    for a in ACTIONS:
        headers = {}
        if a.get("auth") and token:
            headers["X-NOUS-Token"] = token
            headers["Authorization"] = "Bearer " + token

        if a["method"] == "POST":
            r = client.post(a["path"], json={}, headers=headers)
        else:
            r = client.get(a["path"], headers=headers)

        protected_ok = a.get("auth", False) and not token and r.status_code == 401
        ok = (r.status_code < 400) or protected_ok
        data = None
        try:
            data = r.get_json()
        except Exception:
            data = None

        results.append({
            "name": a["name"],
            "method": a["method"],
            "path": a["path"],
            "requires_auth": a.get("auth", False),
            "status": r.status_code,
            "ok": ok,
            "protected_ok": protected_ok,
            "json": r.is_json,
            "error": data.get("error") if isinstance(data, dict) else None,
        })

    return {
        "ok": all(x["ok"] for x in results if not x["requires_auth"]),
        "time": time.time(),
        "total": len(results),
        "passed": len([x for x in results if x["ok"]]),
        "failed": len([x for x in results if not x["ok"]]),
        "results": results,
    }
