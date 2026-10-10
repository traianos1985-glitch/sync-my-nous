"""Fail-closed, atomic storage for object-shaped JSON runtime state."""
from __future__ import annotations

import fcntl
import json
import os
import tempfile
from contextlib import contextmanager


DEFAULT_STATE = {"profile": {}, "goals": [], "projects": [], "decisions": []}


def _validate_state(value, path):
    if not isinstance(value, dict):
        raise RuntimeError(f"json_state_integrity_failure:{path}")
    if not isinstance(value.get("profile"), dict):
        raise RuntimeError(f"json_state_integrity_failure:{path}")
    for key in ("goals", "projects", "decisions"):
        if not isinstance(value.get(key), list) or any(not isinstance(item, dict) for item in value[key]):
            raise RuntimeError(f"json_state_integrity_failure:{path}")
    return value


def _read_unlocked(path):
    if not os.path.exists(path):
        return {key: (value.copy() if isinstance(value, (dict, list)) else value) for key, value in DEFAULT_STATE.items()}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, ValueError, TypeError) as exc:
        raise RuntimeError(f"json_state_integrity_failure:{path}") from exc
    return _validate_state(value, path)


def _write_unlocked(path, state):
    _validate_state(state, path)
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=".object-state-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(state, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
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


@contextmanager
def edit_object(path):
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    with open(path + ".lock", "a", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            state = _read_unlocked(path)
            yield state
            _write_unlocked(path, state)
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def read_object(path):
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    with open(path + ".lock", "a", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            state = _read_unlocked(path)
            return json.loads(json.dumps(state, ensure_ascii=False))
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def write_object(path, state):
    _validate_state(state, path)
    with edit_object(path) as stored:
        stored.clear()
        stored.update(state)
    return state
