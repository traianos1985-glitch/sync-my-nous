"""Opt-in, idempotent fleet rollout queue with optional canary and convergence gates.

Only explicitly mapped provider targets are dispatched. A provider accepting a trigger
is not considered success: a later authenticated heartbeat must report the desired
version and healthy liveness status before the job is marked converged. Canary mode
halts expansion when its configured instances fail to converge or report degradation.
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
_MAX_CANARIES = 10
_MAX_JOBS = 100
_SERVICE_ID = re.compile(r"^[A-Za-z0-9_-]{3,128}$")
_INSTANCE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,79}$")
_RETRY_LIMIT = 3


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
        if not isinstance(instance_id, str) or not _INSTANCE_ID.fullmatch(instance_id):
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


def _canary_ids(targets: dict[str, dict[str, Any]]) -> tuple[list[str], str | None]:
    """Read a bounded, explicit comma-separated canary list; empty preserves legacy mode."""
    raw = os.environ.get("NOUS_FLEET_CANARY_IDS", "").strip()
    if not raw:
        return [], None
    ids = [item.strip() for item in raw.split(",") if item.strip()]
    if not ids or len(ids) > _MAX_CANARIES or len(ids) != len(set(ids)):
        return [], "invalid_canary_ids"
    if any(not _INSTANCE_ID.fullmatch(item) for item in ids):
        return [], "invalid_canary_ids"
    if any(item not in targets for item in ids):
        return [], "canary_target_not_mapped"
    return ids, None


def _reconcile_observed_convergence(status: dict[str, Any], desired: str) -> None:
    """Convert provider-accepted jobs into converged/blocked only from fresh heartbeats."""
    now = time.time()
    instances = {item.get("instance_id"): item for item in status.get("instances", [])}
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT id, instance_id, state FROM fleet_rollout_jobs "
            "WHERE desired_version=? AND state IN ('queued', 'requested', 'dispatching')",
            (desired,),
        ).fetchall()
        for row in rows:
            item = instances.get(row["instance_id"])
            if not item or item.get("stale"):
                continue
            if item.get("reported_status") == "degraded":
                conn.execute(
                    "UPDATE fleet_rollout_jobs SET state='blocked', last_error='post_deploy_degraded', updated_at=? WHERE id=?",
                    (now, row["id"]),
                )
            elif item.get("version") == desired and item.get("reported_status") == "healthy":
                conn.execute(
                    "UPDATE fleet_rollout_jobs SET state='converged', last_error=NULL, updated_at=? WHERE id=?",
                    (now, row["id"]),
                )
        conn.commit()
    finally:
        conn.close()


def _canary_gate(
    status: dict[str, Any], desired: str, canaries: list[str]
) -> tuple[bool, str | None]:
    """Return whether all canaries are fresh, healthy, and running the target release."""
    if not canaries:
        return True, None
    instances = {item.get("instance_id"): item for item in status.get("instances", [])}
    conn = _connect()
    try:
        for canary in canaries:
            item = instances.get(canary)
            if not item or item.get("stale"):
                return False, "canary_convergence_required"
            if item.get("reported_status") == "degraded":
                return False, "canary_health_gate_blocked"
            if item.get("version") != desired or item.get("reported_status") != "healthy":
                return False, "canary_convergence_required"
            job = conn.execute(
                "SELECT state FROM fleet_rollout_jobs WHERE instance_id=? AND desired_version=?",
                (canary, desired),
            ).fetchone()
            if job and job["state"] == "blocked":
                return False, "canary_health_gate_blocked"
            if job and job["state"] not in {"converged"}:
                # If already on the target before this rollout, a healthy heartbeat is
                # enough; otherwise a dispatched job must explicitly converge.
                return False, "canary_convergence_required"
        return True, None
    finally:
        conn.close()


def _queue_drift(
    targets: dict[str, dict[str, Any]],
    desired: str,
    canaries: list[str],
    canary_gate_open: bool,
) -> int:
    status = fleet_status()
    now = time.time()
    queued = 0
    # During canary stage, only canaries may enter the queue. Once all canaries have
    # converged, queue only the remaining fleet; already-current instances are skipped.
    if canaries and not canary_gate_open:
        allowed_ids = set(canaries)
    elif canaries:
        allowed_ids = set(targets) - set(canaries)
    else:
        allowed_ids = set(targets)
    conn = _connect()
    try:
        for item in status.get("instances", []):
            instance_id = item.get("instance_id")
            target = targets.get(instance_id)
            if (instance_id not in allowed_ids or not target or item.get("stale")
                    or not item.get("update_available")):
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
            # Recover abandoned claims and apply bounded retry cooldowns.
            conn.execute(
                """UPDATE fleet_rollout_jobs SET state='failed', last_error='dispatch_timeout', updated_at=?
                WHERE instance_id=? AND desired_version=? AND state='dispatching' AND updated_at < ?""",
                (now, instance_id, desired, now - 300),
            )
            conn.execute(
                """UPDATE fleet_rollout_jobs SET state='queued', last_error=NULL, updated_at=?
                WHERE instance_id=? AND desired_version=? AND state='failed'
                AND attempts < ? AND updated_at < ?""",
                (now, instance_id, desired, _RETRY_LIMIT, now - 900),
            )
            conn.execute(
                """UPDATE fleet_rollout_jobs SET state='queued', last_error=NULL, updated_at=?
                WHERE instance_id=? AND desired_version=? AND state='requested'
                AND attempts < ? AND updated_at < ?""",
                (now, instance_id, desired, _RETRY_LIMIT, now - 1800),
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


def _supersede_obsolete_jobs(desired: str) -> int:
    """Prevent queued or retryable jobs for an older release from being dispatched."""
    conn = _connect()
    try:
        now = time.time()
        cur = conn.execute(
            """UPDATE fleet_rollout_jobs
            SET state='superseded', last_error='superseded_by_new_release', updated_at=?
            WHERE desired_version != ? AND state IN ('queued', 'requested', 'failed')""",
            (now, desired),
        )
        conn.commit()
        return max(0, cur.rowcount)
    finally:
        conn.close()


def _dispatch_one(
    targets: dict[str, dict[str, Any]], desired: str
) -> dict[str, Any]:
    conn = _connect()
    try:
        # Serialize claims across concurrent scheduled invocations.
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT * FROM fleet_rollout_jobs WHERE state='queued' AND desired_version=? ORDER BY created_at, id LIMIT 1",
            (desired,)
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
    """Queue active version drift and dispatch at most one configured deployment."""
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
    canaries, error = _canary_ids(targets)
    if error:
        return {"ok": False, "enabled": True, "error": error}

    _reconcile_observed_convergence(status, str(desired))
    status = fleet_status()
    gate_open, gate_reason = _canary_gate(status, str(desired), canaries)
    if canaries and not gate_open and gate_reason == "canary_health_gate_blocked":
        # A failed/degraded canary halts the entire rollout. No automatic rollback is
        # claimed; an operator must inspect and explicitly remediate the provider.
        return {"ok": True, "enabled": True, "desired_version": desired,
                "mapped_target_count": len(targets), "canary_count": len(canaries),
                "newly_queued": 0, "dispatched": False, "reason": gate_reason}
    _supersede_obsolete_jobs(str(desired))
    queued = _queue_drift(targets, str(desired), canaries, gate_open)
    if canaries and not gate_open:
        # Dispatch canary queue only; non-canaries are not queued until convergence.
        result = _dispatch_one(targets, str(desired))
        if not result.get("dispatched"):
            result["reason"] = gate_reason or "canary_convergence_required"
        return {"ok": True, "enabled": True, "desired_version": desired,
                "mapped_target_count": len(targets), "canary_count": len(canaries),
                "canary_gate_open": False, "newly_queued": queued, **result}
    result = _dispatch_one(targets, str(desired))
    return {"ok": True, "enabled": True, "desired_version": desired,
            "mapped_target_count": len(targets), "canary_count": len(canaries),
            "canary_gate_open": gate_open if canaries else None,
            "newly_queued": queued, **result}


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
    states = ("queued", "dispatching", "requested", "converged", "failed", "blocked", "superseded")
    return {"ok": True, "enabled": _enabled(),
            "canary_ids": [item.strip() for item in os.environ.get("NOUS_FLEET_CANARY_IDS", "").split(",") if item.strip()],
            "jobs": jobs, "counts": {state: sum(job["state"] == state for job in jobs) for state in states}}


def fleet_integration_status() -> dict[str, Any]:
    """Describe platform delivery paths without claiming unprobed live connectivity."""
    status = fleet_status()
    targets, target_error = _targets()
    render_targets = [
        instance_id for instance_id, target in targets.items()
        if target.get("provider") == "render" and target.get("enabled") is True
    ]
    render_key_ready = bool(os.environ.get("RENDER_API_KEY", "").strip())
    render_auto_ready = _enabled() and bool(render_targets) and render_key_ready
    coordinator_token_ready = bool(os.environ.get("NOUS_FLEET_TOKEN", "").strip())
    rollout_token_ready = bool(os.environ.get("NOUS_FLEET_ROLLOUT_TOKEN", "").strip())
    desired_ready = bool(status.get("desired_version"))
    configured_db = os.environ.get("NOUS_FLEET_DB_PATH", "").strip()
    if configured_db:
        storage_path = Path(configured_db).expanduser()
    else:
        storage_path = Path(os.environ.get("NOUS_DATA_DIR", "data")) / "nous_fleet.sqlite3"
    storage_ready = storage_path.parent.exists() and storage_path.parent.is_dir() and os.access(storage_path.parent, os.W_OK)

    platforms = [
        {
            "id": "github",
            "role": "source_control",
            "delivery_mode": "merge_to_main_and_ci",
            "configuration": "repository",
            "state": "source_of_truth",
            "live_verified": False,
            "detail": "Main branch is the shared code source; CI results must be checked in GitHub Actions.",
        },
        {
            "id": "github_pages",
            "role": "static_frontend",
            "delivery_mode": "repository_workflow",
            "configuration": "repository",
            "state": "not_runtime_probed",
            "live_verified": False,
            "detail": "Static frontend updates through its configured repository workflow; it cannot run backend heartbeats.",
        },
        {
            "id": "lovable",
            "role": "git_synced_frontend",
            "delivery_mode": "git_sync",
            "configuration": "repository_link",
            "state": "repository_linked_not_live_verified",
            "live_verified": False,
            "detail": "Lovable follows repository synchronization; this backend cannot verify editor or publish state.",
        },
        {
            "id": "render",
            "role": "central_backend",
            "delivery_mode": "render_api_trigger" if render_auto_ready else "manual_or_report_only",
            "configuration": "server_environment",
            "state": (
                "configured_for_trigger" if render_auto_ready
                else "mapping_or_credentials_missing" if _enabled()
                else "automatic_trigger_disabled"
            ),
            "live_verified": False,
            "enabled_target_count": len(render_targets),
            "detail": "Secret presence and mapping are configuration checks only; provider deployment and runtime health require a later healthy heartbeat.",
        },
        {
            "id": "local_android",
            "role": "local_runtime_and_companion",
            "delivery_mode": "heartbeat_and_client_release",
            "configuration": "per_installation",
            "state": "heartbeat_only",
            "live_verified": False,
            "detail": "Local/Android clients can report metadata when configured; the central server does not silently replace their installed binaries.",
        },
    ]
    checks = [
        {"id": "fleet_token", "ready": coordinator_token_ready},
        {"id": "rollout_token", "ready": rollout_token_ready},
        {"id": "desired_version", "ready": desired_ready},
        {"id": "database_storage", "ready": storage_ready},
        {"id": "render_target_mapping", "ready": not target_error and bool(render_targets)},
        {"id": "render_api_key", "ready": render_key_ready if render_targets else None},
    ]
    blocking = [item["id"] for item in checks if item["ready"] is False]
    return {
        "ok": True,
        "generated_at": time.time(),
        "overall_state": "configured_with_limits" if not blocking else "needs_configuration",
        "checks": checks,
        "blocking_checks": blocking,
        "automatic_deployment_enabled": render_auto_ready,
        "target_version": status.get("desired_version"),
        "fleet": {
            "instance_count": status.get("instance_count", 0),
            "outdated_count": status.get("outdated_count", 0),
            "stale_count": status.get("stale_count", 0),
        },
        "platforms": platforms,
        "limitations": [
            "This endpoint reports repository architecture and server-side configuration, not live GitHub, Pages, Lovable, or provider API connectivity.",
            "A Git merge can trigger configured CI/static-site workflows and Lovable repository sync, but this endpoint cannot confirm their completion.",
            "Only explicit supported provider mappings can trigger a backend deployment; no prompts, conversations, personal data, or API keys are sent through fleet heartbeats.",
            "Automatic rollout remains opt-in and does not claim automatic rollback or a full synthetic health check.",
        ],
    }


def rollout_preflight() -> dict[str, Any]:
    """Return a secret-safe, read-only checklist for operating the fleet controller."""
    from executor.fleet_coordinator import target_version

    targets, target_error = _targets()
    canaries, canary_error = _canary_ids(targets) if not target_error else ([], "deploy_targets_invalid")
    desired = target_version()

    configured_db = os.environ.get("NOUS_FLEET_DB_PATH", "").strip()
    if configured_db:
        db_path = Path(configured_db).expanduser()
    else:
        db_path = Path(os.environ.get("NOUS_DATA_DIR", "data")) / "nous_fleet.sqlite3"
    parent = db_path.parent
    storage_ready = parent.exists() and parent.is_dir() and os.access(parent, os.W_OK)

    required = [
        {"id": "heartbeat_token", "ready": bool(os.environ.get("NOUS_FLEET_TOKEN", "").strip()),
         "detail": "Central heartbeat authentication secret is configured."},
        {"id": "rollout_token", "ready": bool(os.environ.get("NOUS_FLEET_ROLLOUT_TOKEN", "").strip()),
         "detail": "Dedicated scheduled-controller token is configured."},
        {"id": "desired_version", "ready": bool(desired),
         "detail": "A valid target release is configured."},
        {"id": "deploy_targets", "ready": not target_error and bool(targets),
         "detail": target_error or ("Explicit enabled provider mappings are available."
                                   if targets else "No enabled Render/Vercel deployment mappings are configured.")},
        {"id": "canary_configuration", "ready": not canary_error,
         "detail": canary_error or ("Canary configuration is valid." if canaries
                                   else "Canary stage is not configured; one-at-a-time rollout mode will be used.")},
        {"id": "database_storage", "ready": storage_ready,
         "detail": "Configured database directory exists and is writable."
                   if storage_ready else "Database directory is missing or not writable; check persistent storage configuration."},
    ]
    if any(item.get("provider") == "render" for item in targets.values()):
        render_key_ready = bool(os.environ.get("RENDER_API_KEY", "").strip())
        required.append({
            "id": "render_api_key",
            "ready": render_key_ready,
            "detail": "Render API credential is configured." if render_key_ready
                      else "A mapped Render target requires RENDER_API_KEY.",
        })

    fleet_counts = {"instance_count": 0, "outdated_count": 0, "stale_count": 0}
    # Inspect an existing registry in read-only mode; do not create files or schema.
    if db_path.is_file():
        try:
            uri = db_path.resolve().as_uri() + "?mode=ro"
            with sqlite3.connect(uri, uri=True, timeout=2) as connection:
                table = connection.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='fleet_instances'"
                ).fetchone()
                if table:
                    rows = connection.execute(
                        "SELECT version, last_seen FROM fleet_instances LIMIT 500"
                    ).fetchall()
                    now = time.time()
                    fleet_counts["instance_count"] = len(rows)
                    fleet_counts["outdated_count"] = sum(bool(desired and row[0] != desired) for row in rows)
                    fleet_counts["stale_count"] = sum(now - float(row[1]) > 900 for row in rows)
        except (sqlite3.Error, OSError, ValueError):
            pass

    return {
        "ok": True,
        "ready": all(item["ready"] for item in required),
        "automatic_deployment_enabled": _enabled(),
        "desired_version": desired or None,
        "mapped_target_count": len(targets),
        "canary_count": len(canaries),
        "fleet": fleet_counts,
        "checks": required,
        "limitations": [
            "This checklist validates server-side configuration presence and basic storage readiness only.",
            "It cannot verify GitHub Actions secrets, provider build health, successful deployment, or rollback readiness.",
            "A writable directory is not proof of durable storage across host restarts.",
            "Automatic deployment remains disabled unless NOUS_FLEET_AUTO_DEPLOY is explicitly enabled.",
        ],
    }
