import json
import time

from executor.json_state_store import edit_list, read_list, write_list

FILE = "data/decision_memory.json"


def _load():
    return read_list(FILE)


def _save(items):
    return write_list(FILE, items)


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
    with edit_list(FILE) as items:
        ids = {str(existing.get("id")) for existing in items}
        while str(item["id"]) in ids:
            item["id"] += 1
        items.append(item)
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
    return {"time": time.time(), "total": len(items), "recent": items[-10:], "tags": by_tag}


def search_decisions(query="", limit=20):
    q = (query or "").lower()
    items = _load()
    if not q:
        return items[-int(limit):]
    found = [item for item in items if q in json.dumps(item, ensure_ascii=False).lower()]
    return found[-int(limit):]


def remember_system_decision(event, data=None):
    data = data or {}
    return record_decision(
        title=data.get("title") or event,
        reason=data.get("reason") or data.get("description") or "",
        goal_id=data.get("goal_id"),
        mission_id=data.get("mission_id"),
        action=data.get("action"),
        result=data.get("result"),
        confidence=data.get("confidence", 0.75),
        tags=data.get("tags", ["system"]),
    )
