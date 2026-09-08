import json
import os
import time

FILE = "data/agent_journal.json"


def _load():
    if not os.path.exists(FILE):
        return []
    try:
        return json.load(open(FILE, "r", encoding="utf-8"))
    except Exception:
        return []


def _save(items):
    os.makedirs("data", exist_ok=True)
    json.dump(items[-500:], open(FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def write_journal(event, data=None):
    items = _load()
    item = {
        "id": int(time.time_ns()),
        "time": time.time(),
        "event": str(event),
        "data": data or {},
    }
    items.append(item)
    _save(items)
    return item


def list_journal(limit=50):
    return _load()[-int(limit):]
