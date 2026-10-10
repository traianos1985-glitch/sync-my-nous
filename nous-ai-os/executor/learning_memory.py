import json
import time

from executor.json_state_store import edit_list, read_list, write_list

FILE = "data/lessons_learned.json"


def _load():
    return read_list(FILE)


def _save(items):
    return write_list(FILE, items)


def record_lesson(lesson, outcome="success", goal_id=None, mission_id=None, decision_id=None, confidence=0.8, tags=None):
    item = {
        "id": int(time.time_ns()),
        "lesson": lesson,
        "outcome": outcome,
        "goal_id": goal_id,
        "mission_id": mission_id,
        "decision_id": decision_id,
        "confidence": float(confidence),
        "tags": tags or [],
        "created": time.time(),
    }
    with edit_list(FILE) as items:
        ids = {str(existing.get("id")) for existing in items}
        while str(item["id"]) in ids:
            item["id"] += 1
        items.append(item)
    return item


def list_lessons(limit=100):
    return _load()[-int(limit):]


def lesson_status():
    items = _load()
    return {
        "time": time.time(),
        "total": len(items),
        "success": len([item for item in items if item.get("outcome") == "success"]),
        "failure": len([item for item in items if item.get("outcome") == "failure"]),
        "recent": items[-10:],
    }


def search_lessons(query=""):
    q = (query or "").lower()
    results = [item for item in _load() if q in json.dumps(item, ensure_ascii=False).lower()]
    return results[-50:]
