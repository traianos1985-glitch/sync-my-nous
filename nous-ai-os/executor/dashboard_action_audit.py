import time
from concurrent.futures import CancelledError, ThreadPoolExecutor, TimeoutError as FuturesTimeout

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


def _run_action(app, action, headers):
    """Κάθε action σε δικό του thread/client — το test_client δεν είναι thread-safe."""
    client = app.test_client()
    if action["method"] == "POST":
        return client.post(action["path"], json={}, headers=headers)
    return client.get(action["path"], headers=headers)


def _entry(action, status, error, ok=False, protected_ok=False, is_json=False, skipped=False):
    return {
        "name": action["name"],
        "method": action["method"],
        "path": action["path"],
        "requires_auth": action.get("auth", False),
        "status": status,
        "ok": ok,
        "protected_ok": protected_ok,
        "json": is_json,
        "skipped": skipped,
        "error": error,
    }


def dashboard_action_audit(app, token=""):
    """Probe read-only dashboard routes without triggering state-changing actions.

    POST entries in ACTIONS are deliberately reported as skipped. Even with a
    valid owner token, an audit must not create backups, propose missions, start
    schedulers, or otherwise mutate the running NOUS instance.
    """
    action_timeout = 75.0
    budget = 90.0
    started = time.time()
    deadline = started + budget

    results = [
        _entry(action, 0, "skipped_non_read_only", skipped=True)
        for action in ACTIONS
        if action["method"].upper() != "GET"
    ]
    read_only_actions = [action for action in ACTIONS if action["method"].upper() == "GET"]
    pool = ThreadPoolExecutor(max_workers=max(1, len(read_only_actions)))
    futures = []
    try:
        for action in read_only_actions:
            headers = {}
            if token:
                headers["X-NOUS-Token"] = token
                headers["Authorization"] = "Bearer " + token
            futures.append((action, pool.submit(_run_action, app, action, headers)))

        for action, future in futures:
            remaining = deadline - time.time()
            if remaining <= 0:
                future.cancel()
                results.append(_entry(action, 0, "budget_exhausted"))
                continue
            try:
                response = future.result(timeout=min(action_timeout, remaining))
            except FuturesTimeout:
                future.cancel()
                results.append(_entry(action, 0, "timeout"))
                continue
            except CancelledError:
                results.append(_entry(action, 0, "cancelled"))
                continue
            except Exception as exc:  # noqa: BLE001 - the audit itself should not crash
                results.append(_entry(action, 0, f"error:{type(exc).__name__}"))
                continue

            data = None
            try:
                data = response.get_json()
            except Exception:
                data = None
            results.append(
                _entry(
                    action,
                    response.status_code,
                    data.get("error") if isinstance(data, dict) else None,
                    ok=response.status_code < 400,
                    is_json=response.is_json,
                )
            )
    finally:
        pool.shutdown(wait=False, cancel_futures=True)

    evaluated = [item for item in results if not item["skipped"]]
    return {
        "ok": all(item["ok"] for item in evaluated),
        "time": time.time(),
        "durationMs": int((time.time() - started) * 1000),
        "total": len(results),
        "passed": sum(item["ok"] for item in evaluated),
        "failed": sum(not item["ok"] for item in evaluated),
        "skipped": sum(item["skipped"] for item in results),
        "results": results,
    }
