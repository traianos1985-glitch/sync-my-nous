import json
import os
import time

FILE = "data/lessons_learned.json"


def _load():
    if not os.path.exists(FILE):
        return []
    try:
        return json.load(open(FILE, "r", encoding="utf-8"))
    except Exception:
        return []


def _save(items):
    os.makedirs("data", exist_ok=True)
    json.dump(items, open(FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def record_lesson(
    lesson,
    outcome="success",
    goal_id=None,
    mission_id=None,
    decision_id=None,
    confidence=0.8,
    tags=None,
):
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

    items = _load()
    items.append(item)
    _save(items)
    return item


def list_lessons(limit=100):
    return _load()[-int(limit):]


def lesson_status():
    items = _load()
    return {
        "time": time.time(),
        "total": len(items),
        "success": len([x for x in items if x.get("outcome") == "success"]),
        "failure": len([x for x in items if x.get("outcome") == "failure"]),
        "recent": items[-10:],
    }


def search_lessons(query=""):
    q = (query or "").lower()
    results = []

    for item in _load():
        if q in json.dumps(item, ensure_ascii=False).lower():
            results.append(item)

    return results[-50:]
