"""Best-effort runtime metrics with atomic, concurrent-safe snapshots."""
import fcntl
import json
import os
import tempfile
import time
from contextlib import contextmanager

from executor.task_queue import list_queue
from executor.project_progress import project_summary
from executor.autonomy_service import status as service_status
from executor.scheduler_agent import list_schedules
from executor.battery_guard import battery_guard

FILE = "data/runtime_metrics.json"


@contextmanager
def _metrics_lock():
    directory = os.path.dirname(FILE) or "."
    os.makedirs(directory, exist_ok=True)
    with open(FILE + ".lock", "a", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _persist(metrics):
    directory = os.path.dirname(FILE) or "."
    os.makedirs(directory, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=".runtime_metrics.", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(metrics, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, FILE)
    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def _capture(name, collector, errors):
    try:
        return collector()
    except Exception as exc:
        errors[name] = f"{type(exc).__name__}: {str(exc)[:240]}"
        return None


def _count(items, status):
    if not isinstance(items, list):
        return 0
    return sum(isinstance(item, dict) and item.get("status") == status for item in items)


def collect_metrics():
    errors = {}
    queue = _capture("queue", list_queue, errors)
    projects = _capture("projects", project_summary, errors)
    service = _capture("service", service_status, errors)
    schedules = _capture("schedules", list_schedules, errors)
    battery = _capture("battery", battery_guard, errors)

    metrics = {
        "time": time.time(),
        "status": "degraded" if errors else "healthy",
        "component_errors": errors,
        "battery": battery,
        "service": service,
        "queue": {
            "total": len(queue) if isinstance(queue, list) else None,
            "pending": _count(queue, "pending"),
            "running": _count(queue, "running"),
            "done": _count(queue, "done"),
            "failed": _count(queue, "failed"),
        } if isinstance(queue, list) else None,
        "projects": projects,
        "schedules": {
            "total": len(schedules) if isinstance(schedules, list) else None,
            "scheduled": _count(schedules, "scheduled"),
        } if isinstance(schedules, list) else None,
    }

    with _metrics_lock():
        _persist(metrics)
    return metrics
