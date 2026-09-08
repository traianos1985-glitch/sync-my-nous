import json
import os
import threading
import time

from executor.auto_mission_executor import run_auto_mission_executor, auto_mission_executor_status

FILE = "data/auto_mission_scheduler.json"

_thread = None
_stop = threading.Event()


def _load():
    if not os.path.exists(FILE):
        return {
            "enabled": False,
            "interval_seconds": 900,
            "started": None,
            "stopped": None,
            "last_tick": None,
            "ticks": 0,
            "last_result": None,
        }
    try:
        return json.load(open(FILE, "r", encoding="utf-8"))
    except Exception:
        return {
            "enabled": False,
            "interval_seconds": 900,
            "started": None,
            "stopped": None,
            "last_tick": None,
            "ticks": 0,
            "last_result": None,
            "error": "state_load_failed",
        }


def _save(state):
    os.makedirs("data", exist_ok=True)
    json.dump(state, open(FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def _loop():
    while not _stop.is_set():
        state = _load()
        if not state.get("enabled"):
            break

        result = run_auto_mission_executor(
            max_missions=1,
            max_steps_per_mission=1,
            trigger="auto_mission_scheduler",
        )

        state["last_tick"] = time.time()
        state["ticks"] = int(state.get("ticks", 0)) + 1
        state["last_result"] = {
            "ok": result.get("ok"),
            "executed": len(result.get("run", {}).get("executed", [])),
            "skipped": len(result.get("run", {}).get("skipped", [])),
        }
        _save(state)

        interval = int(state.get("interval_seconds", 900))
        if interval < 300:
            interval = 300

        _stop.wait(interval)


def auto_mission_scheduler_status():
    state = _load()
    alive = _thread.is_alive() if _thread else False
    return {
        "time": time.time(),
        "state": state,
        "thread_alive": alive,
        "executor": auto_mission_executor_status(),
        "safe_mode": True,
    }


def start_auto_mission_scheduler(interval_seconds=900):
    global _thread

    interval_seconds = int(interval_seconds)
    if interval_seconds < 300:
        interval_seconds = 300

    state = _load()
    state["enabled"] = True
    state["interval_seconds"] = interval_seconds
    state["started"] = time.time()
    state["stopped"] = None
    _save(state)

    if _thread and _thread.is_alive():
        return {"ok": True, "already_running": True, "status": auto_mission_scheduler_status()}

    _stop.clear()
    _thread = threading.Thread(target=_loop, daemon=True)
    _thread.start()

    return {"ok": True, "started": True, "status": auto_mission_scheduler_status()}


def stop_auto_mission_scheduler():
    state = _load()
    state["enabled"] = False
    state["stopped"] = time.time()
    _save(state)
    _stop.set()
    return {"ok": True, "stopped": True, "status": auto_mission_scheduler_status()}


def run_auto_mission_scheduler_once():
    result = run_auto_mission_executor(
        max_missions=1,
        max_steps_per_mission=1,
        trigger="manual_auto_mission_scheduler_once",
    )

    state = _load()
    state["last_tick"] = time.time()
    state["ticks"] = int(state.get("ticks", 0)) + 1
    state["last_result"] = {
        "ok": result.get("ok"),
        "executed": len(result.get("run", {}).get("executed", [])),
        "skipped": len(result.get("run", {}).get("skipped", [])),
    }
    _save(state)

    return {"ok": True, "result": result, "status": auto_mission_scheduler_status()}


def reconcile_auto_mission_scheduler():
    state = _load()
    alive = _thread.is_alive() if _thread else False

    if state.get("enabled") and not alive:
        return start_auto_mission_scheduler(state.get("interval_seconds", 900))

    return {"ok": True, "resumed": False, "status": auto_mission_scheduler_status()}
