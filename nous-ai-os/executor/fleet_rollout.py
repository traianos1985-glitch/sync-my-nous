"""Opt-in, idempotent fleet rollout queue for supported provider deployment triggers.

The controller only acts on explicitly mapped instances and only when enabled on the
central backend. It never executes remote shell commands or accepts URLs from heartbeats.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from executor.fleet_coordinator import fleet_status

_TRUE = {"1", "true", "yes", "on"}
_MAX_TARGETS = 50
_MAX_JOBS = 100
_SERVICE_ID = re.compile(r"^[A-Za-z0-9_-]{3,128}$")


def _enabled() -> bool:
    return os.environ.get("NOUS_FLEET_AUTO_DEPLOY", "").strip().lower() in _TRUE


def _db_path() -> Path:
    configured = os.environ.get("NOUS_FLEET_DB_PATH", "").strip()
    if configured:
        path = Path(configured).expanduser().resolve()
    else:
        path = (Path(os.environ.get("NOUS_DATA_DIR", "data")) / "nous_fleet.sqlite3").resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path(), timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("""CREATE TABLE IF NOT EXISTS fleet_rollout_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        instance_id TEXT NOT NULL,
        desired_version TEXT NOT NULL,
        provider TEXT NOT NULL,
        state TEXT NOT NULL,
        attempts INTEGER NOT NULL DEFAULT 0,
        created_at REAL NOT NULL,
        updated_at REAL NOT NULL,
        last_error TEXT,
        UNIQUE(instance_id, desired_version)
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_fleet_rollout_state ON fleet_rollout_jobs(state, created_at)")
    conn.commit()
    return conn


def _targets() -> tuple[dict[str, dict[str, Any]], str | None]:
    raw = os.environ.get("NOUS_FLEET_DEPLOY_TARGETS", "").strip()
    if not raw:
        return {}, None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}, "invalid_deploy_targets_json"
    if not isinstance(data, dict) or len(data) > _MAX_TARGETS:
        return {}, "invalid_deploy_targets_shape"
    clean: dict[str, dict[str, Any]] = {}
    for instance_id, value in data.items():
        if not isinstance(instance_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{2,79}", instance_id):
            return {}, "invalid_instance_mapping"
        if not isinstance(value, dict):
            return {}, "invalid_target_mapping"
        provider = str(value.get("provider") or "").strip().lower()
        if provider not in {"render", "vercel"}:
            # Lovable and other Git-connected environments use their native Git sync.
            continue
        if value.get("enabled") is not True:
            continue
        target: dict[str, Any] = {"provider": provider, "enabled": True}
        if provider == "render":
            service_id = str(value.get("service_id") or "").strip()
            if not _SERVICE_ID.fullmatch(service_id):
                return {}, "invalid_render_service_id"
            target["service_id"] = service_id
        if provider == "vercel":
            hook = str(value.get("deploy_hook_url") or "").strip()
            parsed = urllib.parse.urlsplit(hook)
            if (parsed.scheme != "https" or parsed.hostname != "api.vercel.com"
                    or parsed.username or parsed.password or parsed.query or parsed.fragment
                    or not parsed.path.startswith("/v1/integrations/deploy/")):
                return {}, "invalid_vercel_deploy_hook"
            target["deploy_hook_url"] = hook
        clean[instance_id] = target
    return clean, None


def _queue_drift(targets: dict[str, dict[str, Any]], desired: str) -> int:
    status = fleet_status()
    now = time.time()
    queued = 0
    conn = _connect()
    try:
        for item in status.get("instances", []):
            instance_id = item.get("instance_id")
            target = targets.get(instance_id)
            if not target or item.get("stale") or not item.get("update_available"):
                continue
            if item.get("provider") != target["provider"]:
                continue
            cur = conn.execute(
                """INSERT OR IGNORE INTO fleet_rollout_jobs
                (instance_id, desired_version, provider, state, attempts, created_at, updated_at)
                VALUES (?, ?, ?, 'queued', 0, ?, ?)""",
                (instance_id, desired, target["provider"], now, now),
            )
            queued += max(0, cur.rowcount)
            # Reconcile abandoned dispatches and retry bounded failures. A provider
            # accepting a trigger is not proof that the instance converged.
            conn.execute(
                """UPDATE fleet_rollout_jobs SET state='failed', last_error='dispatch_timeout', updated_at=?
                WHERE instance_id=? AND desired_version=? AND state='dispatching' AND updated_at < ?""",
                (now, instance_id, desired, now - 300),
            )
            conn.execute(
                """UPDATE fleet_rollout_jobs SET state='queued', last_error=NULL, updated_at=?
                WHERE instance_id=? AND desired_version=? AND state='failed'
                AND attempts < 3 AND updated_at < ?""",
                (now, instance_id, desired, now - 900),
            )
            conn.execute(
                """UPDATE fleet_rollout_jobs SET state='queued', last_error=NULL, updated_at=?
                WHERE instance_id=? AND desired_version=? AND state='requested'
                AND attempts < 3 AND updated_at < ?""",
                (now, instance_id, desired, now - 1800),
            )
        conn.commit()
    finally:
        conn.close()
    return queued


def _request_render(service_id: str) -> dict[str, Any]:
    token = os.environ.get("RENDER_API_KEY", "").strip()
    if not token:
        return {"ok": False, "error": "render_api_key_not_configured"}
    request = urllib.request.Request(
        f"https://api.render.com/v1/services/{service_id}/deploys",
        data=b'{"clearCache":"do_not_clear"}',
        headers={"Authorization": "Bearer " + token, "Accept": "application/json",
                 "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            body = response.read(16384)
            data = json.loads(body.decode("utf-8")) if body else {}
            return {"ok": 200 <= response.status < 300, "status_code": response.status,
                    "deployment_id": data.get("id") if isinstance(data, dict) else None}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "status_code": exc.code, "error": "render_api_rejected_request"}
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return {"ok": False, "error": "render_api_unreachable_or_invalid_response"}


def _request_vercel(hook_url: str) -> dict[str, Any]:
    # URL is taken only from a server-side mapping and constrained to Vercel's deploy-hook API.
    request = urllib.request.Request(
        hook_url, data=b"", headers={"Accept": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            body = response.read(16384)
            return {"ok": 200 <= response.status < 300, "status_code": response.status}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "status_code": exc.code, "error": "vercel_deploy_hook_rejected"}
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return {"ok": False, "error": "vercel_deploy_hook_unreachable"}


def _dispatch_one(targets: dict[str, dict[str, Any]]) -> dict[str, Any]:
    conn = _connect()
    try:
        # Serialize claims across concurrent scheduled invocations.
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT * FROM fleet_rollout_jobs WHERE state='queued' ORDER BY created_at, id LIMIT 1"
        ).fetchone()
        if row is None:
            conn.commit()
            return {"dispatched": False, "reason": "queue_empty"}
        target = targets.get(row["instance_id"])
        if not target or target.get("provider") != row["provider"]:
            conn.execute("UPDATE fleet_rollout_jobs SET state='failed', last_error='target_mapping_missing', updated_at=? WHERE id=?",
                         (time.time(), row["id"]))
            conn.commit()
            return {"dispatched": False, "reason": "target_mapping_missing"}
        # Mark before the external call so concurrent cron invocations cannot dispatch the same row.
        claimed = conn.execute(
            "UPDATE fleet_rollout_jobs SET state='dispatching', attempts=attempts+1, updated_at=? WHERE id=? AND state='queued'",
            (time.time(), row["id"]),
        )
        if claimed.rowcount != 1:
            conn.commit()
            return {"dispatched": False, "reason": "already_claimed"}
        conn.commit()
    finally:
        conn.close()

    result = (_request_render(target["service_id"]) if target["provider"] == "render"
              else _request_vercel(target["deploy_hook_url"]))
    now = time.time()
    conn = _connect()
    try:
        state = "requested" if result.get("ok") else "failed"
        error = None if result.get("ok") else str(result.get("error") or "provider_request_failed")[:100]
        conn.execute("UPDATE fleet_rollout_jobs SET state=?, last_error=?, updated_at=? WHERE id=? AND state='dispatching'",
                     (state, error, now, row["id"]))
        conn.commit()
    finally:
        conn.close()
    return {
        "dispatched": True, "instance_id": row["instance_id"],
        "desired_version": row["desired_version"], "provider": row["provider"],
        "state": state, "provider_result": result,
    }


def reconcile_and_dispatch() -> dict[str, Any]:
    """Queue active version drift and dispatch at most one configured provider deployment."""
    if not _enabled():
        return {"ok": True, "enabled": False, "queued": 0, "dispatched": False,
                "reason": "automatic_rollout_disabled"}
    status = fleet_status()
    desired = status.get("desired_version")
    if not desired:
        return {"ok": False, "enabled": True, "error": "desired_version_not_configured"}
    targets, error = _targets()
    if error:
        return {"ok": False, "enabled": True, "error": error}
    queued = _queue_drift(targets, str(desired))
    result = _dispatch_one(targets)
    return {"ok": True, "enabled": True, "desired_version": desired,
            "mapped_target_count": len(targets), "newly_queued": queued, **result}


def rollout_status() -> dict[str, Any]:
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT id, instance_id, desired_version, provider, state, attempts, created_at, updated_at, last_error "
            "FROM fleet_rollout_jobs ORDER BY id DESC LIMIT ?", (_MAX_JOBS,)
        ).fetchall()
        jobs = [dict(row) for row in rows]
    finally:
        conn.close()
    return {"ok": True, "enabled": _enabled(), "jobs": jobs,
            "counts": {state: sum(job["state"] == state for job in jobs)
                       for state in ("queued", "dispatching", "requested", "failed")}}
