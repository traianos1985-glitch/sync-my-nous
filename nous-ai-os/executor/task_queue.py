"""Persistent task queue with crash-safe writes and bounded stale-task recovery."""
import json
import os
import tempfile
import time
from pathlib import Path

FILE = "data/agent_queue.json"
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_MAX_RECOVERIES = 2


def _load():
    if not os.path.exists(FILE):
        return []
    try:
        with open(FILE, "r", encoding="utf-8") as handle:
            items = json.load(handle)
    except (OSError, ValueError, TypeError):
        return []
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def _save(items):
    directory = os.path.dirname(FILE) or "."
    os.makedirs(directory, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=".agent_queue.", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(items, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, FILE)
    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def _int_or(value, fallback):
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return fallback


def add_task(title, kind="general", priority=5, payload=None):
    items = _load()
    item = {
        "id": int(time.time_ns()),
        "title": str(title),
        "kind": str(kind),
        "priority": int(priority),
        "payload": payload if isinstance(payload, dict) else {},
        "status": "pending",
        "created": time.time(),
        "started": None,
        "finished": None,
        "attempts": 0,
        "recovery_count": 0,
        "last_error": None,
        "result": None,
    }
    items.append(item)
    _save(items)
    return item


def list_queue(status=None):
    items = _load()
    if status:
        items = [item for item in items if item.get("status") == status]
    return sorted(items, key=lambda item: _int_or(item.get("priority"), 5))


def next_task():
    pending = list_queue("pending")
    return pending[0] if pending else None


def update_task(task_id, **updates):
    items = _load()
    for item in items:
        if str(item.get("id")) == str(task_id):
            item.update(updates)
            _save(items)
            return item
    return None


def clear_queue():
    _save([])
    return {"cleared": True}


def retry_failed(max_attempts=DEFAULT_MAX_ATTEMPTS):
    max_attempts = _int_or(max_attempts, DEFAULT_MAX_ATTEMPTS)
    if max_attempts < 1:
        return {"retried": [], "error": "max_attempts_must_be_positive"}

    items = _load()
    changed = []
    for item in items:
        if item.get("status") != "failed":
            continue
        attempts = max(0, _int_or(item.get("attempts"), 0))
        if attempts >= max_attempts:
            continue
        item.update({
            "status": "pending",
            "last_error": None,
            "started": None,
            "finished": None,
        })
        changed.append(item)

    _save(items)
    return {"retried": changed}


def recover_dead_tasks(max_age_seconds=900, max_recoveries=DEFAULT_MAX_RECOVERIES):
    """Requeue stale running tasks a bounded number of times, then fail closed."""
    try:
        max_age_seconds = float(max_age_seconds)
    except (TypeError, ValueError, OverflowError):
        max_age_seconds = 900.0
    max_recoveries = _int_or(max_recoveries, DEFAULT_MAX_RECOVERIES)
    if max_age_seconds < 0 or max_recoveries < 0:
        return {"recovered": [], "failed": [], "error": "limits_must_be_non_negative"}

    now = time.time()
    items = _load()
    recovered = []
    failed = []

    for item in items:
        if item.get("status") != "running":
            continue
        try:
            started = float(item.get("started") or 0)
        except (TypeError, ValueError, OverflowError):
            started = 0.0
        if not (0 <= started <= now) or now - started < max_age_seconds:
            continue

        recoveries = max(0, _int_or(item.get("recovery_count"), 0))
        item["recovery_count"] = recoveries
        item["last_error"] = "recovered_from_stale_running_state"
        if recoveries < max_recoveries:
            item.update({
                "status": "pending",
                "recovery_count": recoveries + 1,
                "started": None,
            })
            recovered.append(item)
        else:
            item.update({
                "status": "failed",
                "finished": now,
                "last_error": "stale_running_recovery_limit_exceeded",
            })
            failed.append(item)

    _save(items)
    return {"recovered": recovered, "failed": failed}
