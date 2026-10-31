"""Bounded autonomy service with durable state and cross-worker cycle exclusion."""
from executor import portable_fcntl as fcntl
import json
import os
import tempfile
import time
from contextlib import contextmanager

from executor.autonomous_loop import run_once
from executor.battery_guard import battery_guard
from executor.learning_engine import auto_learning_cycle
from executor.master_agent import master_cycle

STATE_FILE = "data/autonomy_service.json"
LOG_FILE = "data/autonomy.log"
DEFAULT_INTERVAL = 300
MIN_INTERVAL = 5
MAX_INTERVAL = 86400


def _default_state():
    return {
        "enabled": False,
        "interval": DEFAULT_INTERVAL,
        "last_heartbeat": None,
        "last_run": None,
        "last_error": None,
        "cycles": 0,
        "emergency_stop": False,
    }


@contextmanager
def _file_lock(path, nonblocking=False):
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        flags = fcntl.LOCK_EX | (fcntl.LOCK_NB if nonblocking else 0)
        try:
            fcntl.flock(handle.fileno(), flags)
        except BlockingIOError:
            yield False
            return
        try:
            yield True
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@contextmanager
def _state_lock():
    with _file_lock(STATE_FILE + ".lock") as acquired:
        if not acquired:  # blocking lock should never reach this branch
            raise RuntimeError("autonomy_state_lock_unavailable")
        yield


def _load_unlocked():
    if not os.path.exists(STATE_FILE):
        return _default_state()
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as handle:
            state = json.load(handle)
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        raise RuntimeError("autonomy_state_integrity_failure") from exc
    if not isinstance(state, dict):
        raise RuntimeError("autonomy_state_integrity_failure")
    if not isinstance(state.get("enabled"), bool):
        raise RuntimeError("autonomy_state_integrity_failure")
    interval = state.get("interval", DEFAULT_INTERVAL)
    if isinstance(interval, bool) or not isinstance(interval, int) or not MIN_INTERVAL <= interval <= MAX_INTERVAL:
        raise RuntimeError("autonomy_state_integrity_failure")
    cycles = state.get("cycles", 0)
    if isinstance(cycles, bool) or not isinstance(cycles, int) or cycles < 0:
        raise RuntimeError("autonomy_state_integrity_failure")
    emergency_stop = state.get("emergency_stop", False)
    if not isinstance(emergency_stop, bool):
        raise RuntimeError("autonomy_state_integrity_failure")
    return {**_default_state(), **state}


def _load():
    with _state_lock():
        return _load_unlocked()


def _save_unlocked(state):
    if not isinstance(state, dict):
        raise ValueError("autonomy_state_must_be_object")
    directory = os.path.dirname(STATE_FILE) or "."
    os.makedirs(directory, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=".autonomy_service.", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(state, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, STATE_FILE)
        try:
            dir_fd = os.open(directory, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except OSError:
            pass
    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def _save(state):
    with _state_lock():
        # Refuse to replace corrupt existing state with a guessed/default state.
        if os.path.exists(STATE_FILE):
            _load_unlocked()
        _save_unlocked(state)


def log_event(event, data=None):
    os.makedirs("data", exist_ok=True)
    item = {"time": time.time(), "event": str(event), "data": data if isinstance(data, dict) else {}}
    with open(LOG_FILE, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, ensure_ascii=False, allow_nan=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return item


def _bounded_interval(interval):
    try:
        value = int(interval)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("invalid_autonomy_interval") from exc
    if not MIN_INTERVAL <= value <= MAX_INTERVAL:
        raise ValueError("autonomy_interval_out_of_range")
    return value


def enable(interval=DEFAULT_INTERVAL):
    interval = _bounded_interval(interval)
    state = _load()
    state["enabled"] = True
    state["emergency_stop"] = False
    state["interval"] = interval
    state["last_heartbeat"] = time.time()
    _save(state)
    log_event("service_enabled", {"interval": interval})
    return state

def emergency_stop(reason="emergency_stop_triggered"):
    state = _load()
    state["enabled"] = False
    state["emergency_stop"] = True
    state["last_heartbeat"] = time.time()
    _save(state)
    log_event("emergency_stop", {"reason": str(reason)})
    try:
        from executor.autonomy import autonomy_state
        autonomy_state.stop()
    except Exception:
        pass
    return state

def recent_events(limit=50):
    try:
        limit = max(1, min(int(limit), 200))
    except (TypeError, ValueError):
        limit = 50
    if not os.path.exists(LOG_FILE):
        return []
    events = []
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as handle:
            lines = handle.readlines()
        for line in reversed(lines[-limit:]):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except OSError:
        return []
    return events


def disable():
    state = _load()
    state["enabled"] = False
    state["last_heartbeat"] = time.time()
    _save(state)
    log_event("service_disabled")
    return state


def status():
    try:
        state = _load()
    except RuntimeError:
        return {
            "enabled": None,
            "status": "degraded",
            "error": "autonomy_state_integrity_failure",
            "log_file": LOG_FILE,
        }
    state["battery"] = battery_guard()
    state["log_file"] = LOG_FILE
    # This module exposes a managed loop entry point; importing it never starts
    # a background worker, so callers can distinguish enabled from running.
    state["loop_running"] = False
    state["loop_mode"] = "managed_cli_or_explicit_run_forever"
    state["status"] = "healthy"
    return state


def heartbeat():
    state = _load()
    state["last_heartbeat"] = time.time()
    _save(state)
    return state


def _run_cycle_locked():
    try:
        state = _load()
    except RuntimeError:
        return {"ok": False, "error": "autonomy_state_integrity_failure", "state": status()}

    if state.get("emergency_stop"):
        log_event("service_skip", {"reason": "emergency_stop"})
        return {"skipped": True, "reason": "emergency_stop", "state": state}

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
    except Exception as exc:
        state["last_error"] = type(exc).__name__
        state["last_heartbeat"] = time.time()
        _save(state)
        log_event("service_cycle_error", {"error": type(exc).__name__})
        return {"ok": False, "error": "autonomy_cycle_failed", "state": state}


def run_cycle():
    """Permit only one autonomous cycle across processes at a time."""
    with _file_lock(STATE_FILE + ".cycle.lock", nonblocking=True) as acquired:
        if not acquired:
            return {"ok": False, "busy": True, "error": "autonomy_cycle_already_running"}
        return _run_cycle_locked()


def run_forever(interval=None):
    state = _load()
    if interval is not None:
        state = enable(_bounded_interval(interval))
    elif not state.get("enabled"):
        state = enable(int(state.get("interval", DEFAULT_INTERVAL)))

    wait = _bounded_interval(state.get("interval", DEFAULT_INTERVAL))
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
    try:
        state = _load()
    except RuntimeError:
        return {
            "ok": False,
            "enabled": None,
            "action": "needs_attention",
            "reason": "autonomy_state_integrity_failure",
        }
    now = time.time()
    last = state.get("last_heartbeat")

    if state.get("emergency_stop"):
        return {"ok": True, "enabled": False, "action": "none", "reason": "emergency_stopped"}
    if not state.get("enabled"):
        return {"ok": True, "enabled": False, "action": "none", "reason": "service_disabled"}
    if not last:
        return {"ok": False, "enabled": True, "action": "needs_attention", "reason": "no_heartbeat"}

    silence = now - float(last)
    if silence > float(max_silence_seconds):
        log_event("watchdog_warning", {"silence": silence})
        return {"ok": False, "enabled": True, "action": "needs_restart", "silence": silence}
    return {"ok": True, "enabled": True, "action": "none", "silence": silence}
