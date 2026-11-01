"""Failure Memory & Recovery Registry for NOUS AI OS.

Records operational and action failures with deduplicated fingerprints,
contextual error classifications, and remediation hints so subsequent agent/mission
cycles do not repeatedly attempt failing strategies without adaptation.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from executor import portable_fcntl as fcntl

FAILURE_MEMORY_FILE = "data/failure_memory.json"
MAX_ENTRIES = 200


def _load_failures() -> list[dict[str, Any]]:
    path = Path(FAILURE_MEMORY_FILE)
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                data = json.load(f)
                return data if isinstance(data, list) else []
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except Exception:
        return []


def _save_failures(entries: list[dict[str, Any]]) -> bool:
    path = Path(FAILURE_MEMORY_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(entries[-MAX_ENTRIES:], f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        os.replace(tmp_path, path)
        return True
    except Exception:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        return False


def record_failure(
    domain: str,
    action: str,
    error: str,
    details: dict[str, Any] | None = None,
    suggested_fix: str | None = None,
) -> dict[str, Any]:
    """Record an operational failure with timestamp, error signature and remediation hint."""
    details = details or {}
    entry = {
        "timestamp": time.time(),
        "domain": str(domain)[:80],
        "action": str(action)[:80],
        "error": str(error)[:200],
        "details": {k: str(v)[:300] for k, v in details.items()} if isinstance(details, dict) else {},
        "suggested_fix": str(suggested_fix)[:200] if suggested_fix else None,
        "occurrences": 1,
    }

    entries = _load_failures()
    # Deduplicate against recent matching domain + action + error
    for existing in reversed(entries[-50:]):
        if (
            existing.get("domain") == entry["domain"]
            and existing.get("action") == entry["action"]
            and existing.get("error") == entry["error"]
        ):
            existing["occurrences"] = existing.get("occurrences", 1) + 1
            existing["last_seen"] = time.time()
            if suggested_fix:
                existing["suggested_fix"] = str(suggested_fix)[:200]
            _save_failures(entries)
            return existing

    entry["last_seen"] = entry["timestamp"]
    entries.append(entry)
    _save_failures(entries)
    return entry


def query_failures(
    domain: str | None = None,
    action: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Retrieve recent recorded failures filtered by domain or action."""
    entries = _load_failures()
    matches = []
    for item in reversed(entries):
        if domain and item.get("domain") != domain:
            continue
        if action and item.get("action") != action:
            continue
        matches.append(item)
        if len(matches) >= max(1, min(limit, 100)):
            break
    return matches


def clear_failure_memory() -> bool:
    """Clear failure registry."""
    return _save_failures([])
