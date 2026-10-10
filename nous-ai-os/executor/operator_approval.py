"Single-use operator approvals with durable, cross-worker state transitions."
import fcntl, json, os, tempfile, time
from contextlib import contextmanager

FILE = "data/operator_approvals.json"
FINAL_STATUSES = {"completed", "failed", "cancelled"}

def _lock_path():
    return FILE + ".lock"

@contextmanager
def _edit_items():
    directory = os.path.dirname(FILE) or "."
    os.makedirs(directory, exist_ok=True)
    with open(_lock_path(), "a", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            items = _load_unlocked()
            yield items
            _save_unlocked(items)
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

def _load_unlocked():
    if not os.path.exists(FILE):
        return []
    try:
        with open(FILE, "r", encoding="utf-8") as handle:
            items = json.load(handle)
    except (OSError, ValueError, TypeError) as exc:
        raise RuntimeError("approval_store_integrity_failure") from exc
    if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
        raise RuntimeError("approval_store_integrity_failure")
    seen = set()
    for item in items:
        key = str(item.get("id"))
        if key == "None" or key in seen or not isinstance(item.get("status"), str):
            raise RuntimeError("approval_store_integrity_failure")
        seen.add(key)
    return items

def _save_unlocked(items):
    directory = os.path.dirname(FILE) or "."
    os.makedirs(directory, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=".operator_approvals.", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(items, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, FILE)
    except Exception:
        try: os.unlink(temp_path)
        except OSError: pass
        raise

def request_approval(action, payload=None, reason="operator action"):
    action = str(action).strip()
    if not action: raise ValueError("action_must_not_be_empty")
    if payload is not None and not isinstance(payload, dict): raise ValueError("payload_must_be_object")
    item = {"id": int(time.time_ns()), "action": action, "payload": payload.copy() if payload is not None else {}, "reason": str(reason), "status": "pending", "created": time.time(), "decided": None}
    with _edit_items() as items:
        ids = {str(entry.get("id")) for entry in items}
        while str(item["id"]) in ids: item["id"] += 1
        items.append(item)
    return item

def list_approvals(status=None):
    with _edit_items() as items: result = list(items)
    return [item for item in result if item.get("status") == status] if status else result

def get_approval(approval_id):
    return next((item for item in list_approvals() if str(item.get("id")) == str(approval_id)), None)

def approve(approval_id):
    with _edit_items() as items:
        for item in items:
            if str(item.get("id")) == str(approval_id) and item.get("status") == "pending":
                item["status"], item["decided"] = "approved", time.time()
                return item.copy()
    return None

def reject(approval_id):
    with _edit_items() as items:
        for item in items:
            if str(item.get("id")) == str(approval_id) and item.get("status") == "pending":
                item["status"], item["decided"] = "rejected", time.time()
                return item.copy()
    return None

def claim_approved_approval(approval_id, action, payload):
    if not isinstance(payload, dict): return None
    with _edit_items() as items:
        for item in items:
            if str(item.get("id")) == str(approval_id) and item.get("action") == action and item.get("payload") == payload and item.get("status") == "approved":
                item["status"], item["execution_started"] = "executing", time.time()
                return item.copy()
    return None

def finish_approval(approval_id, status, result=None):
    if status not in FINAL_STATUSES: raise ValueError("invalid_final_approval_status")
    with _edit_items() as items:
        for item in items:
            if str(item.get("id")) == str(approval_id) and item.get("status") == "executing":
                item.update(status=status, result=result, finished=time.time())
                return item.copy()
    return None

def is_approved(approval_id):
    item = get_approval(approval_id)
    return bool(item and item.get("status") == "approved")
