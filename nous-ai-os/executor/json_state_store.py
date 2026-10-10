"""Durable, fail-closed JSON list storage for small runtime state files."""
from __future__ import annotations

import fcntl
import json
import os
import tempfile
from contextlib import contextmanager


def _read_unlocked(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            items = json.load(handle)
    except (OSError, ValueError, TypeError) as exc:
        raise RuntimeError(f"json_state_integrity_failure:{path}") from exc
    if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
        raise RuntimeError(f"json_state_integrity_failure:{path}")
    return items


def _write_unlocked(path, items):
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=".json-state-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(items, handle, ensure_ascii=False, indent=2, allow_nan=False)
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
def edit_list(path):
    """Lock, validate and atomically persist a list only if the edit succeeds."""
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    with open(path + ".lock", "a", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            items = _read_unlocked(path)
            yield items
            _write_unlocked(path, items)
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def read_list(path):
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    with open(path + ".lock", "a", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            return list(_read_unlocked(path))
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def write_list(path, items):
    if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
        raise ValueError("json_state_must_be_list_of_objects")
    with edit_list(path) as stored:
        stored[:] = items
    return items
