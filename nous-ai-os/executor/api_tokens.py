import json
import os
import time
import secrets
import hashlib
import threading

FILE = "data/api_tokens.json"
_LOCK = threading.Lock()
# Γράφουμε το last_used το πολύ μία φορά ανά token / 60s (λιγότερο disk I/O
# και λιγότερα races όταν έρχονται πολλά requests μαζί).
_LAST_USED_THROTTLE = 60.0


def _load():
    if not os.path.exists(FILE):
        return []
    try:
        return json.load(open(FILE, "r", encoding="utf-8"))
    except Exception:
        return []


def _save(tokens):
    os.makedirs("data", exist_ok=True)
    tmp = FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(tokens, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, FILE)  # atomic write: δεν χάνονται tokens σε crash


def _hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def active_tokens():
    return [t for t in _load() if not t.get("revoked")]


def has_active_tokens():
    return len(active_tokens()) > 0


def token_stats():
    tokens = _load()
    return {
        "total": len(tokens),
        "active": len([t for t in tokens if not t.get("revoked")]),
        "revoked": len([t for t in tokens if t.get("revoked")]),
    }


def create_token(name="remote"):
    token = "nous_" + secrets.token_urlsafe(32)
    item = {
        "id": int(time.time_ns()),
        "name": str(name).strip() or "remote",
        "token_hash": _hash(token),
        "created": time.time(),
        "revoked": False,
        "last_used": None,
    }

    tokens = _load()
    tokens.append(item)
    _save(tokens)

    return {
        "id": item["id"],
        "name": item["name"],
        "token": token,
        "created": item["created"],
    }


def list_tokens():
    return [
        {
            "id": item.get("id"),
            "name": item.get("name"),
            "created": item.get("created"),
            "revoked": item.get("revoked", False),
            "last_used": item.get("last_used"),
        }
        for item in _load()
    ]


def revoke_token(token_id):
    tokens = _load()
    found = False

    for item in tokens:
        if str(item.get("id")) == str(token_id):
            item["revoked"] = True
            found = True

    _save(tokens)
    return {"revoked": found, "id": token_id}


def token_allowed(token):
    if not token:
        return False

    h = _hash(str(token))
    now = time.time()

    with _LOCK:
        tokens = _load()

        for item in tokens:
            if item.get("revoked"):
                continue

            stored = str(item.get("token_hash") or "")
            if len(stored) == len(h) and secrets.compare_digest(stored, h):
                last = item.get("last_used") or 0
                if now - float(last) > _LAST_USED_THROTTLE:
                    item["last_used"] = now
                    _save(tokens)
                return True

    return False
