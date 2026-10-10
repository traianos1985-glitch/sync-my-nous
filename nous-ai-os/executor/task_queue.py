"""Concurrent-safe persistent task queue with bounded stale-task recovery."""
import fcntl
import json
import os
import tempfile
import time
from contextlib import contextmanager

FILE = "data/agent_queue.json"
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_MAX_RECOVERIES = 2


@contextmanager
def _queue_lock():
    directory = os.path.dirname(FILE) or "."
    os.makedirs(directory, exist_ok=True)
    lock_path = FILE + ".lock"
    with open(lock_path, "a", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)


def _load_unlocked():
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


def inspect_queue_store():
    """Read-only integrity summary of the persisted queue before filtered loading."""
    with _queue_lock():
        if not os.path.exists(FILE):
            return {"status": "healthy", "record_count": 0, "malformed_records": 0}
        try:
            with open(FILE, "r", encoding="utf-8") as handle:
                raw = json.load(handle)
        except (OSError, ValueError, TypeError) as exc:
            return {
                "status": "degraded",
                "error": f"queue_store_unreadable:{type(exc).__name__}",
                "record_count": 0,
                "malformed_records": 0,
            }
        if not isinstance(raw, list):
            return {
                "status": "degraded",
                "error": "queue_store_not_a_list",
                "record_count": 0,
                "malformed_records": 0,
            }
        malformed = sum(not isinstance(item, dict) for item in raw)
        return {
            "status": "degraded" if malformed else "healthy",
            "record_count": len(raw),
            "malformed_records": malformed,
        }


def _save_unlocked(items):
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
    with _queue_lock():
        items = _load_unlocked()
        existing_ids = {str(entry.get("id")) for entry in items}
        while str(item["id"]) in existing_ids:
            item["id"] += 1
        items.append(item)
        _save_unlocked(items)
    return item


def list_queue(status=None):
    with _queue_lock():
        items = _load_unlocked()
    if status:
        items = [item for item in items if item.get("status") == status]
    return sorted(items, key=lambda item: _int_or(item.get("priority"), 5))


def next_task():
    pending = list_queue("pending")
    return pending[0] if pending else None


def update_task(task_id, **updates):
    with _queue_lock():
        items = _load_unlocked()
        for item in items:
            if str(item.get("id")) == str(task_id):
                item.update(updates)
                _save_unlocked(items)
                return item
    return None


def clear_queue():
    with _queue_lock():
        _save_unlocked([])
    return {"cleared": True}


def retry_failed(max_attempts=DEFAULT_MAX_ATTEMPTS):
    max_attempts = _int_or(max_attempts, DEFAULT_MAX_ATTEMPTS)
    if max_attempts < 1:
        return {"retried": [], "error": "max_attempts_must_be_positive"}

    with _queue_lock():
        items = _load_unlocked()
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
        _save_unlocked(items)
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
    recovered = []
    failed = []
    with _queue_lock():
        items = _load_unlocked()
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
            if recoveries < max_recoveries:
                item.update({
                    "status": "pending",
                    "recovery_count": recoveries + 1,
                    "started": None,
                    "last_error": "recovered_from_stale_running_state",
                })
                recovered.append(item.copy())
            else:
                item.update({
                    "status": "failed",
                    "finished": now,
                    "last_error": "stale_running_recovery_limit_exceeded",
                })
                failed.append(item.copy())
        _save_unlocked(items)
    return {"recovered": recovered, "failed": failed}
