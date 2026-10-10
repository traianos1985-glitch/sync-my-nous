"""Truthful, bounded diagnostics for NOUS runtime subsystems."""
from __future__ import annotations

import math
import shutil
import time
from typing import Any, Callable


def _component(name: str, check: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        result = check()
        if not isinstance(result, dict):
            return {"name": name, "status": "unavailable", "error": "invalid_check_result"}
        return {"name": name, **result}
    except Exception as exc:
        return {"name": name, "status": "unavailable", "error": f"{type(exc).__name__}: {str(exc)[:240]}"}


def _disk_check() -> dict[str, Any]:
    usage = shutil.disk_usage(".")
    used_percent = round((usage.used / usage.total) * 100, 1) if usage.total else 0.0
    free_mb = round(usage.free / (1024 * 1024), 1)
    status = "degraded" if free_mb < 256 or used_percent >= 95 else "healthy"
    return {
        "status": status,
        "free_mb": free_mb,
        "used_percent": used_percent,
        "total_mb": round(usage.total / (1024 * 1024), 1),
    }


def _journal_check() -> dict[str, Any]:
    from executor.agent_journal import verify_journal

    result = verify_journal()
    if not isinstance(result, dict) or result.get("ok") is not True:
        return {"status": "degraded", "integrity": result if isinstance(result, dict) else {"ok": False}}
    return {"status": "healthy", "integrity": result}


def _queue_check() -> dict[str, Any]:
    from executor.task_queue import inspect_queue_store, list_queue

    store = inspect_queue_store()
    items = list_queue()
    counts = {"pending": 0, "running": 0, "done": 0, "failed": 0, "other": 0}
    stale_running = 0
    now = time.time()
    for item in items:
        status = item.get("status")
        if isinstance(status, str) and status in counts:
            counts[status] += 1
        else:
            counts["other"] += 1
        if status == "running":
            try:
                started = float(item.get("started") or 0)
            except (TypeError, ValueError, OverflowError):
                started = 0
            if not math.isfinite(started) or started <= 0 or started > now or now - started >= 900:
                stale_running += 1
    degraded = (
        store.get("status") != "healthy"
        or counts["failed"] > 0
        or stale_running > 0
        or counts["other"] > 0
    )
    return {
        "status": "degraded" if degraded else "healthy",
        "counts": counts,
        "stale_running": stale_running,
        "store_integrity": store,
    }


def _mission_check() -> dict[str, Any]:
    from executor.mission_system import list_missions, mission_status
    from executor.mission_integrity import audit_missions

    result = mission_status()
    if not isinstance(result, dict):
        return {"status": "unavailable", "error": "invalid_mission_status"}
    blocked = int(result.get("blocked", 0) or 0)
    active = int(result.get("active", 0) or 0)
    done = int(result.get("done", 0) or 0)
    integrity = audit_missions(list_missions())
    degraded = blocked > 0 or integrity.get("ok") is not True
    return {
        "status": "degraded" if degraded else "healthy",
        "counts": {"total": int(result.get("total", 0) or 0), "active": active, "done": done, "blocked": blocked},
        "integrity": integrity,
    }


def collect_diagnostics() -> dict[str, Any]:
    """Return independent component results; one broken subsystem cannot hide the rest."""
    checks = [
        _component("disk", _disk_check),
        _component("audit_journal", _journal_check),
        _component("task_queue", _queue_check),
        _component("missions", _mission_check),
    ]
    statuses = {item.get("status") for item in checks}
    overall = "healthy" if statuses == {"healthy"} else "degraded"
    return {
        "ok": overall == "healthy",
        "status": overall,
        "timestamp": time.time(),
        "components": checks,
        "summary": {
            "healthy": sum(item.get("status") == "healthy" for item in checks),
            "degraded": sum(item.get("status") == "degraded" for item in checks),
            "unavailable": sum(item.get("status") == "unavailable" for item in checks),
            "total": len(checks),
        },
    }
