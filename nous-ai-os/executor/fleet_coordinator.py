"""Central registry for NOUS installations and desired-version drift.

The coordinator records metadata only. It does not execute code, trigger deployments,
or accept arbitrary callbacks/URLs from remote installations.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from pathlib import Path
from typing import Any

_INSTANCE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,79}$")
_PROVIDER_ID = re.compile(r"^[a-z][a-z0-9_-]{1,31}$")
_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+/-]{0,119}$")
_MAX_INSTANCES = 500
_STALE_AFTER_SECONDS = 15 * 60
_MIN_INSTANCE_TOKEN_LENGTH = 32


def fleet_auth_configuration() -> dict[str, Any]:
    """Validate per-instance heartbeat credentials without exposing secret values."""
    raw = os.environ.get("NOUS_FLEET_INSTANCE_TOKENS")
    if raw is None or not raw.strip():
        ready = bool(os.environ.get("NOUS_FLEET_TOKEN", "").strip())
        return {"mode": "legacy_shared" if ready else "misconfigured", "ready": ready, "instance_count": 0}
    try:
        mapping = json.loads(raw)
    except (TypeError, ValueError):
        return {"mode": "misconfigured", "ready": False, "instance_count": 0}
    if not isinstance(mapping, dict) or not mapping or len(mapping) > _MAX_INSTANCES:
        return {"mode": "misconfigured", "ready": False, "instance_count": 0}
    for instance_id, token in mapping.items():
        if (not isinstance(instance_id, str) or not _INSTANCE_ID.fullmatch(instance_id)
                or not isinstance(token, str) or not (_MIN_INSTANCE_TOKEN_LENGTH <= len(token) <= 512)
                or token.strip() != token):
            return {"mode": "misconfigured", "ready": False, "instance_count": 0}
    return {"mode": "per_instance", "ready": True, "instance_count": len(mapping)}


def _database_path() -> Path:
    configured = os.environ.get("NOUS_FLEET_DB_PATH", "").strip()
    if configured:
        path = Path(configured).expanduser().resolve()
    else:
        path = (Path(os.environ.get("NOUS_DATA_DIR", "data")) / "nous_fleet.sqlite3").resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(_database_path(), timeout=5)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 5000")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


def _initialize(connection: sqlite3.Connection) -> None:
    connection.execute("""CREATE TABLE IF NOT EXISTS fleet_instances (
        instance_id TEXT PRIMARY KEY,
        provider TEXT NOT NULL,
        version TEXT NOT NULL,
        commit_sha TEXT,
        status TEXT NOT NULL,
        first_seen REAL NOT NULL,
        last_seen REAL NOT NULL
    )""")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_fleet_last_seen ON fleet_instances(last_seen)")
    connection.commit()


def _auto_deploy_enabled() -> bool:
    return os.environ.get("NOUS_FLEET_AUTO_DEPLOY", "").strip().lower() in {"1", "true", "yes", "on"}


def _render_target_enabled(instance_id: str, provider: str) -> bool:
    """Check whether this exact instance has a valid, explicit Render mapping."""
    if provider != "render" or not _auto_deploy_enabled():
        return False
    if not os.environ.get("RENDER_API_KEY", "").strip():
        return False
    try:
        targets = json.loads(os.environ.get("NOUS_FLEET_DEPLOY_TARGETS", "{}"))
    except (TypeError, ValueError):
        return False
    if not isinstance(targets, dict):
        return False
    target = targets.get(instance_id)
    return bool(
        isinstance(target, dict)
        and target.get("provider") == "render"
        and target.get("enabled") is True
        and re.fullmatch(r"[A-Za-z0-9_-]{3,128}", str(target.get("service_id") or ""))
    )


def _update_mode(instance_id: str, provider: str) -> str:
    if _render_target_enabled(instance_id, provider):
        return "provider_triggered"
    return "report_only"


def target_version() -> str:
    value = os.environ.get("NOUS_FLEET_TARGET_VERSION", os.environ.get("NOUS_VERSION", "")).strip()
    return value if value and _VERSION.fullmatch(value) else ""


def current_version() -> str:
    value = (os.environ.get("RENDER_GIT_COMMIT") or os.environ.get("VERCEL_GIT_COMMIT_SHA")
             or os.environ.get("GITHUB_SHA") or os.environ.get("NOUS_VERSION") or "unknown").strip()
    return value[:120] if _VERSION.fullmatch(value) else "unknown"


def record_heartbeat(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"ok": False, "error": "json_object_required"}
    instance_id = str(payload.get("instance_id") or "").strip()
    provider = str(payload.get("provider") or "generic").strip().lower()
    version = str(payload.get("version") or "unknown").strip()
    commit_sha = str(payload.get("commit_sha") or "").strip()
    status = str(payload.get("status") or "unknown").strip().lower()
    if not _INSTANCE_ID.fullmatch(instance_id):
        return {"ok": False, "error": "invalid_instance_id"}
    if not _PROVIDER_ID.fullmatch(provider):
        return {"ok": False, "error": "invalid_provider"}
    if not _VERSION.fullmatch(version) or (commit_sha and not re.fullmatch(r"[A-Fa-f0-9]{7,64}", commit_sha)):
        return {"ok": False, "error": "invalid_version_metadata"}
    if status not in {"healthy", "degraded", "unknown"}:
        return {"ok": False, "error": "invalid_status"}

    now = time.time()
    desired = target_version()
    with _connect() as connection:
        _initialize(connection)
        existing = connection.execute("SELECT first_seen FROM fleet_instances WHERE instance_id = ?", (instance_id,)).fetchone()
        if existing is None:
            count = connection.execute("SELECT COUNT(*) FROM fleet_instances").fetchone()[0]
            if count >= _MAX_INSTANCES:
                return {"ok": False, "error": "fleet_capacity_reached"}
            first_seen = now
        else:
            first_seen = float(existing["first_seen"])
        connection.execute("""INSERT INTO fleet_instances
            (instance_id, provider, version, commit_sha, status, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(instance_id) DO UPDATE SET provider=excluded.provider,
            version=excluded.version, commit_sha=excluded.commit_sha,
            status=excluded.status, last_seen=excluded.last_seen""",
            (instance_id, provider, version, commit_sha or None, status, first_seen, now))
        connection.commit()
    return {
        "ok": True, "instance_id": instance_id, "received_at": now,
        "desired_version": desired or None,
        "update_available": bool(desired and version != desired),
        "update_mode": _update_mode(instance_id, provider),
        "automatic_deployment_enabled": _render_target_enabled(instance_id, provider),
    }


def fleet_status(now: float | None = None) -> dict[str, Any]:
    current_time = time.time() if now is None else float(now)
    desired = target_version()
    with _connect() as connection:
        _initialize(connection)
        rows = connection.execute("""SELECT instance_id, provider, version, commit_sha,
            status, first_seen, last_seen FROM fleet_instances ORDER BY instance_id LIMIT ?""",
            (_MAX_INSTANCES,)).fetchall()
    instances = []
    for row in rows:
        seen = float(row["last_seen"])
        stale = current_time - seen > _STALE_AFTER_SECONDS
        instances.append({
            "instance_id": row["instance_id"], "provider": row["provider"],
            "version": row["version"], "commit_sha": row["commit_sha"],
            "reported_status": row["status"], "first_seen": row["first_seen"],
            "last_seen": seen, "stale": stale,
            "update_available": bool(desired and row["version"] != desired),
            "update_mode": _update_mode(row["instance_id"], row["provider"]),
            "automatic_deployment_enabled": _render_target_enabled(row["instance_id"], row["provider"]),
        })
    return {
        "ok": True, "desired_version": desired or None,
        "update_mode": ("provider_triggered" if any(
            item["automatic_deployment_enabled"] for item in instances
        ) else "report_only"),
        "automatic_deployment_enabled": any(
            item["automatic_deployment_enabled"] for item in instances
        ),
        "stale_after_seconds": _STALE_AFTER_SECONDS,
        "instance_count": len(instances),
        "outdated_count": sum(item["update_available"] for item in instances),
        "stale_count": sum(item["stale"] for item in instances),
        "instances": instances,
    }


def clear_fleet_registry_for_tests() -> None:
    """Test helper: remove the SQLite database and its WAL sidecars."""
    path = _database_path()
    for suffix in ("", "-wal", "-shm"):
        try:
            Path(str(path) + suffix).unlink()
        except FileNotFoundError:
            pass
