"""Concurrent-safe, bounded, hash-chained agent audit journal."""
import fcntl
import hashlib
import json
import os
import tempfile
import time
from contextlib import contextmanager

FILE = "data/agent_journal.json"
MAX_ENTRIES = 500


@contextmanager
def _locked():
    directory = os.path.dirname(FILE) or "."
    os.makedirs(directory, exist_ok=True)
    # The sidecar inode remains stable while the data file is atomically replaced.
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
    fd, temp_path = tempfile.mkstemp(prefix=".agent_journal.", suffix=".tmp", dir=directory)
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


def _digest(event, data, previous):
    payload = {"event": event, "data": data, "previous": previous}
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def write_journal(event, data=None):
    event = str(event)
    payload_data = data if data is not None else {}
    with _locked():
        items = _load_unlocked()
        previous = items[-1].get("hash", "") if items else ""
        item = {
            "id": int(time.time_ns()),
            "time": time.time(),
            "event": event,
            "data": payload_data,
            "previous": previous,
        }
        item["hash"] = _digest(item["event"], item["data"], item["previous"])
        items.append(item)
        _save_unlocked(items)
    return item


def list_journal(limit=50):
    try:
        limit = max(1, min(int(limit), MAX_ENTRIES))
    except (TypeError, ValueError, OverflowError):
        limit = 50
    with _locked():
        return _load_unlocked()[-limit:]


def verify_journal():
    with _locked():
        items = _load_unlocked()

    previous = None
    for index, item in enumerate(items):
        event = item.get("event", "")
        data = item.get("data", {})
        # The first retained entry may point to an older entry removed by retention.
        # Its stored previous hash is the anchor; every following link is verified.
        link = item.get("previous", "") if index == 0 else previous
        expected = _digest(event, data, link)
        if item.get("previous", "") != link or item.get("hash") != expected:
            return {"ok": False, "error": "journal_integrity_failed", "id": item.get("id")}
        previous = item.get("hash")
    return {"ok": True, "entries": len(items)}
