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
        # Exception text can contain paths, request data or secrets.
        error_type = type(exc).__name__
        return {"name": name, "status": "unavailable", "error": error_type}


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
    ok = isinstance(result, dict) and result.get("ok") is True
    # Expose only a minimal integrity summary; raw journal diagnostics may include
    # paths or event metadata that should not be copied into a broad health API.
    integrity: dict[str, Any] = {"ok": ok}
    if isinstance(result, dict):
        for key in ("entries_checked", "valid_entries", "invalid_entries"):
            value = result.get(key)
            if isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 10_000_000:
                integrity[key] = value
    return {"status": "healthy" if ok else "degraded", "integrity": integrity}


def _queue_check() -> dict[str, Any]:
    from executor.task_queue import inspect_queue_store, list_queue

    store = inspect_queue_store()
    raw_items = list_queue()
    items = raw_items if isinstance(raw_items, list) else []
    counts = {"pending": 0, "running": 0, "done": 0, "failed": 0, "other": 0}
    stale_running = 0
    malformed = 0
    now = time.time()
    # Health reporting must remain bounded even if persisted queue state grows
    # unexpectedly. A truncated scan is reported as degraded, never healthy.
    scan_limit = 2_000
    truncated = len(items) > scan_limit
    for item in items[:scan_limit]:
        if not isinstance(item, dict):
            counts["other"] += 1
            malformed += 1
            continue
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
    store_status = store.get("status") if isinstance(store, dict) else "unavailable"
    degraded = (
        store_status != "healthy"
        or counts["failed"] > 0
        or stale_running > 0
        or counts["other"] > 0
        or truncated
    )
    return {
        "status": "degraded" if degraded else "healthy",
        "counts": counts,
        "stale_running": stale_running,
        "malformed_items": malformed,
        "scanned_items": min(len(items), scan_limit),
        "truncated": truncated,
        "store_integrity": {"status": store_status},
    }


def _mission_check() -> dict[str, Any]:
    from executor.mission_system import list_missions, mission_status
    from executor.mission_integrity import audit_missions

    result = mission_status()
    if not isinstance(result, dict):
        return {"status": "unavailable", "error": "invalid_mission_status"}

    def safe_count(value: Any) -> int:
        try:
            count = int(value or 0)
        except (TypeError, ValueError, OverflowError):
            return 0
        return min(max(count, 0), 10_000_000)

    counts = {
        name: safe_count(result.get(name, 0))
        for name in ("total", "active", "done", "blocked")
    }
    integrity_result = audit_missions(list_missions())
    integrity_ok = isinstance(integrity_result, dict) and integrity_result.get("ok") is True
    integrity = {"ok": integrity_ok}
    if isinstance(integrity_result, dict):
        for key in ("checked", "invalid", "duplicates"):
            value = integrity_result.get(key)
            if isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 10_000_000:
                integrity[key] = value
    degraded = counts["blocked"] > 0 or not integrity_ok
    return {
        "status": "degraded" if degraded else "healthy",
        "counts": counts,
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
