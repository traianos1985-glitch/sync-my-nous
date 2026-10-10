"""Concurrent-safe bounded action log."""
import fcntl
import json
import os
import tempfile
import time
from contextlib import contextmanager

FILE = "data/action_log.json"
MAX_ENTRIES = 300


@contextmanager
def _locked():
    directory = os.path.dirname(FILE) or "."
    os.makedirs(directory, exist_ok=True)
    with open(FILE + ".lock", "a", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


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


def _save_unlocked(items):
    directory = os.path.dirname(FILE) or "."
    os.makedirs(directory, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=".action_log.", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(items[-MAX_ENTRIES:], handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, FILE)
    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def log_action(action, result=None):
    item = {"time": time.time(), "action": action, "result": result}
    with _locked():
        items = _load_unlocked()
        items.append(item)
        _save_unlocked(items)
    return item


def recent_actions():
    with _locked():
        return _load_unlocked()[-20:]
