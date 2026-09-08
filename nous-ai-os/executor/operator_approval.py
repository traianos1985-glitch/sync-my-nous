import json, os, time

FILE = "data/operator_approvals.json"

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

def request_approval(action, payload=None, reason="operator action"):
    items = _load()
    item = {
        "id": int(time.time_ns()),
        "action": str(action),
        "payload": payload or {},
        "reason": reason,
        "status": "pending",
        "created": time.time(),
        "decided": None,
    }
    items.append(item)
    _save(items)
    return item

def list_approvals(status=None):
    items = _load()
    if status:
        items = [x for x in items if x.get("status") == status]
    return items

def approve(approval_id):
    items = _load()
    for item in items:
        if str(item.get("id")) == str(approval_id):
            item["status"] = "approved"
            item["decided"] = time.time()
            _save(items)
            return item
    return None

def reject(approval_id):
    items = _load()
    for item in items:
        if str(item.get("id")) == str(approval_id):
            item["status"] = "rejected"
            item["decided"] = time.time()
            _save(items)
            return item
    return None

def is_approved(approval_id):
    item = next((x for x in _load() if str(x.get("id")) == str(approval_id)), None)
    return bool(item and item.get("status") == "approved")
