import json
import os
import time

FILE = "data/executive_memory_v3.json"


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


def remember_event(title, what_happened="", why="", result="", tags=None, avoid_repeating=False):
    item = {
        "id": int(time.time_ns()),
        "created": time.time(),
        "title": title,
        "what_happened": what_happened,
        "why": why,
        "result": result,
        "tags": tags or [],
        "avoid_repeating": bool(avoid_repeating),
    }
    items = _load()

    key = (title, result, tuple(sorted(tags or [])))
    for x in items:
        if (x.get("title"), x.get("result"), tuple(sorted(x.get("tags", [])))) == key:
            return {"ok": True, "deduped": True, "memory": x}

    items.append(item)
    items = items[-500:]
    _save(items)
    return {"ok": True, "memory": item}


def executive_memory_status():
    items = _load()
    return {
        "time": time.time(),
        "total": len(items),
        "avoid_repeating": len([x for x in items if x.get("avoid_repeating")]),
        "recent": items[-20:],
    }


def search_executive_memory(query=""):
    q = (query or "").lower()
    items = _load()
    if not q:
        return items[-50:]
    return [x for x in items if q in json.dumps(x, ensure_ascii=False).lower()][-50:]


def learn_from_recent_state():
    created = []

    try:
        from executor.pending_review import pending_review_status
        p = pending_review_status()
        if p.get("total", 0) > 5:
            created.append(remember_event(
                title="Pending inbox is getting crowded",
                what_happened="Pending review has %s items." % p.get("total"),
                why="Repeated loops can create too many pending items if deduplication is weak.",
                result="Use cleanup engine and deduplication before creating more proposals.",
                tags=["pending", "dedup", "cleanup"],
                avoid_repeating=True,
            ))
    except Exception:
        pass

    try:
        from executor.self_diagnosis import self_diagnosis_status
        d = self_diagnosis_status()
        report = d.get("report", {})
        if report.get("ok"):
            created.append(remember_event(
                title="Self diagnosis passed",
                what_happened="Compile, endpoints and dashboard audit passed.",
                why="System health is stable.",
                result="Do not generate repair patches unless a real problem appears.",
                tags=["diagnosis", "stable"],
                avoid_repeating=True,
            ))
    except Exception:
        pass

    return {"ok": True, "created": created, "status": executive_memory_status()}
