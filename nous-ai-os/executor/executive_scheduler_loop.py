import json
import os
import threading
import time

from executor.executive_scheduler import run_executive_review

STATE_FILE = "data/executive_scheduler_loop.json"

_thread = None
_stop_event = threading.Event()


def _load_state():
    if not os.path.exists(STATE_FILE):
        return {
            "enabled": False,
            "interval_seconds": 1800,
            "last_run": None,
            "last_result": None,
            "started": None,
            "stopped": None,
            "runs": 0,
        }
    try:
        return json.load(open(STATE_FILE, "r", encoding="utf-8"))
    except Exception:
        return {
            "enabled": False,
            "interval_seconds": 1800,
            "last_run": None,
            "last_result": None,
            "started": None,
            "stopped": None,
            "runs": 0,
            "error": "state_load_failed",
        }


def _save_state(state):
    os.makedirs("data", exist_ok=True)
    json.dump(state, open(STATE_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def _loop():
    while not _stop_event.is_set():
        state = _load_state()

        if not state.get("enabled"):
            break

        result = run_executive_review("scheduler_loop")

        state["last_run"] = time.time()
        state["last_result"] = {
            "ok": result.get("ok"),
            "review_id": result.get("review", {}).get("id"),
            "next_best_action": result.get("review", {}).get("next_best_action"),
        }
        state["runs"] = int(state.get("runs", 0)) + 1
        _save_state(state)

        interval = int(state.get("interval_seconds", 1800))
        if interval < 60:
            interval = 60

        _stop_event.wait(interval)


def scheduler_loop_status():
    state = _load_state()
    alive = _thread.is_alive() if _thread else False

    return {
        "time": time.time(),
        "state": state,
        "thread_alive": alive,
        "safe_mode": True,
        "does_not_auto_execute": [
            "approvals",
            "deployments",
            "android_taps",
            "destructive_actions",
        ],
    }


def start_scheduler_loop(interval_seconds=1800):
    global _thread

    interval_seconds = int(interval_seconds)
    if interval_seconds < 60:
        interval_seconds = 60

    state = _load_state()
    state["enabled"] = True
    state["interval_seconds"] = interval_seconds
    state["started"] = time.time()
    state["stopped"] = None
    _save_state(state)

    if _thread and _thread.is_alive():
        return {
            "ok": True,
            "already_running": True,
            "status": scheduler_loop_status(),
        }

    _stop_event.clear()
    _thread = threading.Thread(target=_loop, daemon=True)
    _thread.start()

    return {
        "ok": True,
        "started": True,
        "status": scheduler_loop_status(),
    }


def stop_scheduler_loop():
    state = _load_state()
    state["enabled"] = False
    state["stopped"] = time.time()
    _save_state(state)

    _stop_event.set()

    return {
        "ok": True,
        "stopped": True,
        "status": scheduler_loop_status(),
    }


def run_scheduler_once():
    result = run_executive_review("manual_scheduler_once")
    state = _load_state()
    state["last_run"] = time.time()
    state["last_result"] = {
        "ok": result.get("ok"),
        "review_id": result.get("review", {}).get("id"),
        "next_best_action": result.get("review", {}).get("next_best_action"),
    }
    state["runs"] = int(state.get("runs", 0)) + 1
    _save_state(state)

    return {
        "ok": True,
        "result": result,
        "status": scheduler_loop_status(),
    }


def reconcile_scheduler_loop_state():
    """
    If state says enabled=true but no thread is alive, resume the safe scheduler loop.
    This runs no dangerous action directly; it only restarts the review loop.
    """
    state = _load_state()
    alive = _thread.is_alive() if _thread else False

    if state.get("enabled") and not alive:
        return start_scheduler_loop(state.get("interval_seconds", 1800))

    return {
        "ok": True,
        "resumed": False,
        "status": scheduler_loop_status(),
    }
