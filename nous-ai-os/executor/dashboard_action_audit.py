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


def _entry(action, status, error, ok=False, protected_ok=False, is_json=False):
    return {
        "name": action["name"],
        "method": action["method"],
        "path": action["path"],
        "requires_auth": action.get("auth", False),
        "status": status,
        "ok": ok,
        "protected_ok": protected_ok,
        "json": is_json,
        "error": error,
    }


def dashboard_action_audit(app, token=""):
    """Τρέχει όλα τα dashboard actions και επιστρέφει το score τους.

    Στο Render κάθε sub-request παίρνει δευτερόλεπτα και τα authenticated
    actions κάνουν πραγματική δουλειά, οπότε η σειριακή εκτέλεση έσπαγε το
    gunicorn timeout (120s) και το endpoint απαντούσε 500. Τρέχουμε
    συγχρόνισμα με αυστηρό συνολικό budget κάτω από αυτό το όριο, και ό,τι δεν
    προλαβαίνει σημειώνεται ρητά ως timeout/budget_exhausted — δεν κρύβεται.
    """
    action_timeout = 12.0
    budget = 90.0
    started = time.time()
    deadline = started + budget

    pool = ThreadPoolExecutor(max_workers=6)
    futures = []
    try:
        for action in ACTIONS:
            headers = {}
            # Το fail-closed guard απαιτεί token σε ΟΛΑ τα endpoints (όχι μόνο σε
            # όσα έχουν auth=True), αλλιώς τα περισσότερα actions αποτυγχάνουν με
            # 401 και το audit αναφέρει ψεύτικα σφάλματα.
            if token:
                headers["X-NOUS-Token"] = token
                headers["Authorization"] = "Bearer " + token
            futures.append((action, pool.submit(_run_action, app, action, headers)))

        results = []
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
            except Exception as exc:  # noqa: BLE001 - το audit δεν πρέπει να πέφτει ποτέ
                results.append(_entry(action, 0, f"error:{type(exc).__name__}"))
                continue

            data = None
            try:
                data = response.get_json()
            except Exception:
                data = None
            protected_ok = action.get("auth", False) and not token and response.status_code == 401
            results.append(
                _entry(
                    action,
                    response.status_code,
                    data.get("error") if isinstance(data, dict) else None,
                    ok=(response.status_code < 400) or protected_ok,
                    protected_ok=protected_ok,
                    is_json=response.is_json,
                )
            )
    finally:
        pool.shutdown(wait=False, cancel_futures=True)

    return {
        "ok": all(x["ok"] for x in results if not x["requires_auth"]),
        "time": time.time(),
        "durationMs": int((time.time() - started) * 1000),
        "total": len(results),
        "passed": len([x for x in results if x["ok"]]),
        "failed": len([x for x in results if not x["ok"]]),
        "results": results,
    }
