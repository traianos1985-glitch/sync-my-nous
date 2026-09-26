import hashlib
import json
import os
import time

FILE = "data/agent_journal.json"


def _load():
    if not os.path.exists(FILE):
        return []
    try:
        return json.loads(open(FILE, "r", encoding="utf-8").read())
    except (OSError, json.JSONDecodeError):
        return []


def _save(items):
    os.makedirs(os.path.dirname(FILE) or ".", exist_ok=True)
    temp = f"{FILE}.tmp"
    with open(temp, "w", encoding="utf-8") as handle:
        json.dump(items[-500:], handle, ensure_ascii=False, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, FILE)


def write_journal(event, data=None):
    items = _load()
    previous = items[-1].get("hash", "") if items else ""
    payload = {"event": str(event), "data": data or {}, "previous": previous}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    item = {"id": int(time.time_ns()), "time": time.time(), **payload, "hash": digest}
    items.append(item)
    _save(items)
    return item


def list_journal(limit=50):
    return _load()[-max(1, min(int(limit), 500)):]


def verify_journal():
    previous = ""
    for item in _load():
        payload = {"event": item.get("event", ""), "data": item.get("data", {}), "previous": previous}
        expected = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        if item.get("hash") != expected:
            return {"ok": False, "error": "journal_integrity_failed", "id": item.get("id")}
        previous = item["hash"]
    return {"ok": True, "entries": len(_load())}
