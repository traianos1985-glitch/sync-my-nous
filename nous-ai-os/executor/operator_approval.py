import fcntl
import json
import os
import time
from contextlib import contextmanager

FILE = "data/operator_approvals.json"


def _load():
    if not os.path.exists(FILE):
        return []
    try:
        with open(FILE, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return []


def _save(items):
    os.makedirs("data", exist_ok=True)
    with open(FILE, "w", encoding="utf-8") as handle:
        json.dump(items, handle, ensure_ascii=False, indent=2)


@contextmanager
def _edit_items():
    os.makedirs(os.path.dirname(FILE), exist_ok=True)
    with open(FILE, "a+", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        items = _load()
        try:
            yield items
        except Exception:
            raise
        else:
            _save(items)


def request_approval(action, payload=None, reason="operator action"):
    item = {
        "id": int(time.time_ns()),
        "action": str(action),
        "payload": payload or {},
        "reason": reason,
        "status": "pending",
        "created": time.time(),
        "decided": None,
    }
    with _edit_items() as items:
        items.append(item)
    return item


def list_approvals(status=None):
    items = _load()
    if status:
        items = [x for x in items if x.get("status") == status]
    return items


def get_approval(approval_id):
    return next((x for x in _load() if str(x.get("id")) == str(approval_id)), None)


def approve(approval_id):
    with _edit_items() as items:
        for item in items:
            if str(item.get("id")) == str(approval_id) and item.get("status") == "pending":
                item["status"] = "approved"
                item["decided"] = time.time()
                return item
    return None


def reject(approval_id):
    with _edit_items() as items:
        for item in items:
            if str(item.get("id")) == str(approval_id) and item.get("status") == "pending":
                item["status"] = "rejected"
                item["decided"] = time.time()
                return item
    return None


def claim_approved_approval(approval_id, action, payload):
    with _edit_items() as items:
        for item in items:
            if (
                str(item.get("id")) == str(approval_id)
                and item.get("action") == action
                and item.get("payload") == payload
                and item.get("status") == "approved"
            ):
                item["status"] = "executing"
                item["execution_started"] = time.time()
                return item
    return None


def finish_approval(approval_id, status, result=None):
    with _edit_items() as items:
        for item in items:
            if str(item.get("id")) == str(approval_id) and item.get("status") == "executing":
                item["status"] = status
                item["result"] = result
                item["finished"] = time.time()
                return item
    return None


def is_approved(approval_id):
    item = get_approval(approval_id)
    return bool(item and item.get("status") == "approved")
