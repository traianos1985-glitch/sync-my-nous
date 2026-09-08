import json
import os
import time
from pathlib import Path

from executor.autonomous_loop import run_once
from executor.battery_guard import battery_guard
from executor.learning_engine import auto_learning_cycle
from executor.master_agent import master_cycle

STATE_FILE = "data/autonomy_service.json"
LOG_FILE = "data/autonomy.log"


def _load():
    if not os.path.exists(STATE_FILE):
        return {
            "enabled": False,
            "interval": 300,
            "last_heartbeat": None,
            "last_run": None,
            "last_error": None,
            "cycles": 0,
        }
    try:
        return json.load(open(STATE_FILE, "r", encoding="utf-8"))
    except Exception:
        return {
            "enabled": False,
            "interval": 300,
            "last_heartbeat": None,
            "last_run": None,
            "last_error": "state_load_failed",
            "cycles": 0,
        }


def _save(state):
    os.makedirs("data", exist_ok=True)
    json.dump(state, open(STATE_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def log_event(event, data=None):
    os.makedirs("data", exist_ok=True)
    item = {
        "time": time.time(),
        "event": event,
        "data": data or {},
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")
    return item


def enable(interval=300):
    state = _load()
    state["enabled"] = True
    state["interval"] = int(interval)
    state["last_heartbeat"] = time.time()
    _save(state)
    log_event("service_enabled", {"interval": int(interval)})
    return state


def disable():
    state = _load()
    state["enabled"] = False
    state["last_heartbeat"] = time.time()
    _save(state)
    log_event("service_disabled")
    return state


def status():
    state = _load()
    state["battery"] = battery_guard()
    state["log_file"] = LOG_FILE
    return state


def heartbeat():
    state = _load()
    state["last_heartbeat"] = time.time()
    _save(state)
    return state


def run_cycle():
    state = _load()

    if not state.get("enabled"):
        log_event("service_skip", {"reason": "disabled"})
        return {"skipped": True, "reason": "disabled", "state": state}

    try:
        result = run_once()
        result["learning"] = auto_learning_cycle()
        result["master"] = master_cycle(real_research=False)
        state["last_run"] = time.time()
        state["last_error"] = None
        state["cycles"] = int(state.get("cycles", 0)) + 1
        state["last_heartbeat"] = time.time()
        _save(state)
        log_event("service_cycle_ok", {"keys": list(result.keys()) if isinstance(result, dict) else []})
        return {"ok": True, "result": result, "state": state}
    except Exception as e:
        state["last_error"] = str(e)
        state["last_heartbeat"] = time.time()
        _save(state)
        log_event("service_cycle_error", {"error": str(e)})
        return {"ok": False, "error": str(e), "state": state}


def run_forever(interval=None):
    state = _load()
    if interval is not None:
        state = enable(int(interval))
    elif not state.get("enabled"):
        state = enable(int(state.get("interval", 300)))

    wait = int(state.get("interval", 300))
    log_event("service_loop_started", {"interval": wait})

    while _load().get("enabled"):
        run_cycle()
        time.sleep(wait)

    log_event("service_loop_stopped")
    return status()


if __name__ == "__main__":
    import sys

    interval = None
    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
        except ValueError:
            interval = None

    print("NOUS autonomy service started. CTRL+C to stop.")
    try:
        run_forever(interval)
    except KeyboardInterrupt:
        disable()
        print("NOUS autonomy service stopped.")


def watchdog_check(max_silence_seconds=900):
    state = _load()
    now = time.time()
    last = state.get("last_heartbeat")

    if not state.get("enabled"):
        return {
            "ok": True,
            "enabled": False,
            "action": "none",
            "reason": "service_disabled",
        }

    if not last:
        return {
            "ok": False,
            "enabled": True,
            "action": "needs_attention",
            "reason": "no_heartbeat",
        }

    silence = now - float(last)

    if silence > float(max_silence_seconds):
        log_event("watchdog_warning", {"silence": silence})
        return {
            "ok": False,
            "enabled": True,
            "action": "needs_restart",
            "silence": silence,
        }

    return {
        "ok": True,
        "enabled": True,
        "action": "none",
        "silence": silence,
    }
