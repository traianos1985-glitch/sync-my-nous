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


def _read_raw_unlocked():
    """Read persisted data without silently filtering corruption."""
    if not os.path.exists(FILE):
        return [], None
    try:
        with open(FILE, "r", encoding="utf-8") as handle:
            items = json.load(handle)
    except (OSError, ValueError, TypeError) as exc:
        return None, f"journal_store_unreadable:{type(exc).__name__}"
    if not isinstance(items, list):
        return None, "journal_store_not_a_list"
    if any(not isinstance(item, dict) for item in items):
        return None, "journal_store_malformed_record"
    return items, None


def _load_unlocked():
    # Compatibility loader for legacy read-only callers. Integrity-sensitive paths
    # must use _read_raw_unlocked instead.
    items, error = _read_raw_unlocked()
    return items if error is None else []


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


def _load():
    """Compatibility wrapper for existing diagnostics and tests."""
    with _locked():
        return _load_unlocked()


def _save(items):
    """Compatibility wrapper; callers still get serialized atomic writes."""
    with _locked():
        _save_unlocked(items)


def _digest(event, data, previous):
    payload = {"event": event, "data": data, "previous": previous}
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _verify_items(items):
    previous = None
    for index, item in enumerate(items):
        event = item.get("event", "")
        data = item.get("data", {})
        stored_previous = item.get("previous", "")
        stored_hash = item.get("hash")
        if not isinstance(event, str) or not isinstance(stored_previous, str) or not isinstance(stored_hash, str):
            return {"ok": False, "error": "journal_integrity_failed", "id": item.get("id")}
        # The first retained entry may point to an older entry removed by retention.
        # Its stored previous hash is the anchor; every following link is verified.
        link = stored_previous if index == 0 else previous
        try:
            expected = _digest(event, data, link)
        except (TypeError, ValueError, OverflowError):
            return {"ok": False, "error": "journal_integrity_failed", "id": item.get("id")}
        if stored_previous != link or stored_hash != expected:
            return {"ok": False, "error": "journal_integrity_failed", "id": item.get("id")}
        previous = stored_hash
    return {"ok": True, "entries": len(items)}


def _inspect_unlocked():
    items, error = _read_raw_unlocked()
    if error:
        return {"ok": False, "error": "journal_store_integrity_failure", "detail": error}
    return _verify_items(items)


def write_journal(event, data=None):
    event = str(event)
    payload_data = data if data is not None else {}
    with _locked():
        integrity = _inspect_unlocked()
        if integrity.get("ok") is not True:
            # Never replace a damaged audit history with a fresh/partial chain.
            raise RuntimeError("journal_integrity_failure")
        items, _ = _read_raw_unlocked()
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
        return _inspect_unlocked()
