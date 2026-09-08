import json
import os
import time

FILE = "data/decision_memory.json"


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


def record_decision(title, reason="", goal_id=None, mission_id=None, action=None, result=None, confidence=0.7, tags=None):
    item = {
        "id": int(time.time_ns()),
        "title": title,
        "reason": reason,
        "goal_id": goal_id,
        "mission_id": mission_id,
        "action": action,
        "result": result,
        "confidence": float(confidence),
        "tags": tags or [],
        "created": time.time(),
    }

    items = _load()
    items.append(item)
    _save(items)
    return item


def list_decisions(limit=50):
    items = _load()
    return items[-int(limit):]


def decision_status():
    items = _load()
    by_tag = {}
    for item in items:
        for tag in item.get("tags", []):
            by_tag[tag] = by_tag.get(tag, 0) + 1

    return {
        "time": time.time(),
        "total": len(items),
        "recent": items[-10:],
        "tags": by_tag,
    }


def search_decisions(query="", limit=20):
    q = (query or "").lower()
    items = _load()

    if not q:
        return items[-int(limit):]

    found = []
    for item in items:
        hay = json.dumps(item, ensure_ascii=False).lower()
        if q in hay:
            found.append(item)

    return found[-int(limit):]


def remember_system_decision(event, data=None):
    data = data or {}
    title = data.get("title") or event
    reason = data.get("reason") or data.get("description") or ""
    goal_id = data.get("goal_id")
    mission_id = data.get("mission_id")
    action = data.get("action")
    result = data.get("result")
    confidence = data.get("confidence", 0.75)
    tags = data.get("tags", ["system"])

    return record_decision(
        title=title,
        reason=reason,
        goal_id=goal_id,
        mission_id=mission_id,
        action=action,
        result=result,
        confidence=confidence,
        tags=tags,
    )
