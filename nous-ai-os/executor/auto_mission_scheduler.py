"""Fail-closed, atomic persistence for the autonomous mission scheduler."""
from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

from executor.auto_mission_executor import (
    auto_mission_executor_status,
    run_auto_mission_executor,
)

FILE = Path("data/auto_mission_scheduler.json")
_MIN_INTERVAL_SECONDS = 300
_MAX_INTERVAL_SECONDS = 86400
_STATE_LOCK = threading.RLock()
_thread: threading.Thread | None = None
_stop = threading.Event()


def _default_state() -> dict[str, Any]:
    return {
        "enabled": False,
        "interval_seconds": 900,
        "started": None,
        "stopped": None,
        "last_tick": None,
        "ticks": 0,
        "last_result": None,
    }


def _validate_state(state: Any) -> dict[str, Any]:
    if not isinstance(state, dict) or not isinstance(state.get("enabled"), bool):
        raise ValueError("auto_mission_scheduler_state_invalid")
    interval = state.get("interval_seconds")
    ticks = state.get("ticks")
    if (
        isinstance(interval, bool)
        or not isinstance(interval, int)
        or not _MIN_INTERVAL_SECONDS <= interval <= _MAX_INTERVAL_SECONDS
        or isinstance(ticks, bool)
        or not isinstance(ticks, int)
        or ticks < 0
    ):
        raise ValueError("auto_mission_scheduler_state_invalid")
    for key in ("started", "stopped", "last_tick"):
        value = state.get(key)
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, (int, float))
        ):
            raise ValueError("auto_mission_scheduler_state_invalid")
    result = state.get("last_result")
    if result is not None and not isinstance(result, dict):
        raise ValueError("auto_mission_scheduler_state_invalid")
    normalized = _default_state()
    normalized.update(state)
    return normalized


def _load() -> dict[str, Any]:
    path = Path(FILE)
    if not path.exists():
        return _default_state()
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("auto_mission_scheduler_state_unavailable") from exc
    return _validate_state(parsed)


def _save(state: dict[str, Any]) -> None:
    normalized = _validate_state(state)
    path = Path(FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = handle.name
            json.dump(normalized, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
        temp_path = None
        try:
            directory_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except OSError:
            pass
    except (OSError, TypeError, ValueError) as exc:
        raise ValueError("auto_mission_scheduler_state_write_failed") from exc
    finally:
        if temp_path:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass


def _result_summary(result: Any) -> dict[str, Any]:
    if not isinstance(result, dict):
        return {"ok": False, "executed": 0, "skipped": 0}
    run = result.get("run") if isinstance(result.get("run"), dict) else {}
    executed, skipped = run.get("executed", []), run.get("skipped", [])
    return {
        "ok": bool(result.get("ok")),
        "executed": len(executed) if isinstance(executed, list) else 0,
        "skipped": len(skipped) if isinstance(skipped, list) else 0,
    }


def _loop() -> None:
    while not _stop.is_set():
        try:
            with _STATE_LOCK:
                state = _load()
            if not state["enabled"]:
                break
            result = run_auto_mission_executor(
                max_missions=1,
                max_steps_per_mission=1,
                trigger="auto_mission_scheduler",
            )
            with _STATE_LOCK:
                state = _load()
                if not state["enabled"]:
                    break
                state["last_tick"] = time.time()
                state["ticks"] += 1
                state["last_result"] = _result_summary(result)
                _save(state)
            _stop.wait(state["interval_seconds"])
        except ValueError:
            # Corrupt/unavailable state must stop autonomy, never reset itself.
            break
        except Exception:
            # Transient executor errors do not justify rewriting scheduler state.
            _stop.wait(_MIN_INTERVAL_SECONDS)


def auto_mission_scheduler_status() -> dict[str, Any]:
    alive = _thread.is_alive() if _thread else False
    try:
        with _STATE_LOCK:
            state = _load()
        return {
            "ok": True,
            "time": time.time(),
            "state": state,
            "thread_alive": alive,
            "executor": auto_mission_executor_status(),
            "safe_mode": True,
        }
    except ValueError as exc:
        return {
            "ok": False,
            "time": time.time(),
            "state": None,
            "thread_alive": alive,
            "executor": None,
            "safe_mode": True,
            "status": "unavailable",
            "error": str(exc),
        }


def start_auto_mission_scheduler(interval_seconds: int = 900) -> dict[str, Any]:
    global _thread
    if isinstance(interval_seconds, bool) or not isinstance(interval_seconds, int):
        return {"ok": False, "error": "invalid_interval_seconds"}
    interval_seconds = max(_MIN_INTERVAL_SECONDS, interval_seconds)
    if interval_seconds > _MAX_INTERVAL_SECONDS:
        return {"ok": False, "error": "invalid_interval_seconds"}

    with _STATE_LOCK:
        try:
            state = _load()
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}
        if _thread and _thread.is_alive():
            return {
                "ok": True,
                "already_running": True,
                "status": auto_mission_scheduler_status(),
            }
        state["enabled"] = True
        state["interval_seconds"] = interval_seconds
        state["started"] = time.time()
        state["stopped"] = None
        try:
            _save(state)
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}
        _stop.clear()
        _thread = threading.Thread(
            target=_loop, daemon=True, name="nous_auto_mission_scheduler"
        )
        _thread.start()
    return {"ok": True, "started": True, "status": auto_mission_scheduler_status()}


def stop_auto_mission_scheduler() -> dict[str, Any]:
    _stop.set()
    with _STATE_LOCK:
        try:
            state = _load()
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}
        state["enabled"] = False
        state["stopped"] = time.time()
        try:
            _save(state)
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}
    return {"ok": True, "stopped": True, "status": auto_mission_scheduler_status()}


def run_auto_mission_scheduler_once() -> dict[str, Any]:
    try:
        with _STATE_LOCK:
            _load()
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    result = run_auto_mission_executor(
        max_missions=1,
        max_steps_per_mission=1,
        trigger="manual_auto_mission_scheduler_once",
    )
    try:
        with _STATE_LOCK:
            state = _load()
            state["last_tick"] = time.time()
            state["ticks"] += 1
            state["last_result"] = _result_summary(result)
            _save(state)
    except ValueError as exc:
        return {"ok": False, "error": str(exc), "result": result}
    return {
        "ok": bool(isinstance(result, dict) and result.get("ok")),
        "result": result,
        "status": auto_mission_scheduler_status(),
    }


def reconcile_auto_mission_scheduler() -> dict[str, Any]:
    try:
        with _STATE_LOCK:
            state = _load()
    except ValueError as exc:
        return {"ok": False, "error": str(exc), "status": auto_mission_scheduler_status()}
    alive = _thread.is_alive() if _thread else False
    if state.get("enabled") and not alive:
        return start_auto_mission_scheduler(state["interval_seconds"])
    return {"ok": True, "resumed": False, "status": auto_mission_scheduler_status()}
