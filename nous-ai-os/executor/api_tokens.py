"""Concurrent-safe API token store with fail-closed corruption handling."""
from __future__ import annotations
from executor import portable_fcntl as fcntl
import hashlib, json, os, secrets, tempfile, threading, time
from contextlib import contextmanager

FILE = "data/api_tokens.json"
_LOCK = threading.Lock()
_LAST_USED_THROTTLE = 60.0
MAX_TOKENS = 500
VALID_SCOPES = {"user", "admin"}


@contextmanager
def _store_lock():
    """Serialize token-store operations across threads and worker processes."""
    directory = os.path.dirname(FILE) or "."
    os.makedirs(directory, exist_ok=True)
    with _LOCK:
        with open(FILE + ".lock", "a", encoding="utf-8") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _load_unlocked():
    if not os.path.exists(FILE):
        return []
    try:
        with open(FILE, "r", encoding="utf-8") as handle:
            items = json.load(handle)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("api_token_store_corrupt") from exc
    if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
        raise RuntimeError("api_token_store_corrupt")
    if any(not isinstance(item.get("token_hash"), str) or not item["token_hash"] for item in items):
        raise RuntimeError("api_token_store_corrupt")
    return items


def _save_unlocked(tokens):
    directory = os.path.dirname(FILE) or "."
    os.makedirs(directory, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=".api_tokens.", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(tokens, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, FILE)
        try:
            dir_fd = os.open(directory, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except OSError:
            pass
    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def _hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def active_tokens():
    with _store_lock():
        return [item for item in _load_unlocked() if not item.get("revoked")]


def has_active_tokens():
    return bool(active_tokens())


def token_stats():
    with _store_lock():
        tokens = _load_unlocked()
        return {"total": len(tokens), "active": sum(not x.get("revoked") for x in tokens),
                "revoked": sum(bool(x.get("revoked")) for x in tokens)}


def create_token(name="remote", scope="user"):
    safe_name = str(name).strip()[:80] or "remote"
    safe_scope = str(scope).strip().lower()
    if safe_scope not in VALID_SCOPES:
        raise ValueError("invalid_token_scope")
    with _store_lock():
        tokens = _load_unlocked()
        if len(tokens) >= MAX_TOKENS:
            raise RuntimeError("api_token_limit_reached")
        token = "nous_" + secrets.token_urlsafe(32)
        item = {"id": int(time.time_ns()), "name": safe_name, "scope": safe_scope,
                "token_hash": _hash(token), "created": time.time(), "revoked": False, "last_used": None}
        existing_ids = {str(value.get("id")) for value in tokens}
        while str(item["id"]) in existing_ids:
            item["id"] += 1
        tokens.append(item)
        _save_unlocked(tokens)
    return {"id": item["id"], "name": item["name"], "scope": item["scope"],
            "token": token, "created": item["created"]}


def list_tokens():
    with _store_lock():
        tokens = _load_unlocked()
        return [{"id": x.get("id"), "name": x.get("name"), "scope": x.get("scope", "user"),
                 "created": x.get("created"), "revoked": x.get("revoked", False),
                 "last_used": x.get("last_used")} for x in tokens]


def revoke_token(token_id):
    with _store_lock():
        tokens = _load_unlocked()
        found = False
        for item in tokens:
            if str(item.get("id")) == str(token_id) and not item.get("revoked"):
                item["revoked"] = True
                found = True
        if found:
            _save_unlocked(tokens)
    return {"revoked": found, "id": token_id}


def token_allowed(token, required_scope="user"):
    if not token or required_scope not in VALID_SCOPES:
        return False
    candidate_hash = _hash(str(token))
    now = time.time()
    with _store_lock():
        tokens = _load_unlocked()
        changed = False
        allowed = False
        for item in tokens:
            if item.get("revoked"):
                continue
            stored = item["token_hash"]
            scope = item.get("scope", "user")
            scope_allowed = scope == "admin" or (required_scope == "user" and scope == "user")
            if scope_allowed and len(stored) == len(candidate_hash) and secrets.compare_digest(stored, candidate_hash):
                allowed = True
                if now - float(item.get("last_used") or 0) > _LAST_USED_THROTTLE:
                    item["last_used"] = now
                    changed = True
                break
        if changed:
            _save_unlocked(tokens)
        return allowed
