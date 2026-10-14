"""Read-only runtime lifecycle planning for portable, long-lived NOUS deployments.

This module reports evidence and recommendations only. It never provisions
resources, installs packages, starts background keep-alive loops, or deploys.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any, Mapping

_PROVIDER_ENV = {
    "vercel": ("VERCEL", "VERCEL_ENV", "VERCEL_URL", "VERCEL_PROJECT_ID"),
    "render": ("RENDER", "RENDER_SERVICE_ID", "RENDER_INSTANCE_ID"),
    "railway": ("RAILWAY_PROJECT_ID", "RAILWAY_SERVICE_ID", "RAILWAY_ENVIRONMENT_ID"),
    "replit": ("REPL_ID", "REPLIT_DB_URL", "REPLIT_DEPLOYMENT"),
    "codespaces": ("CODESPACES", "CODESPACE_NAME"),
    "lovable": ("LOVABLE", "LOVABLE_PROJECT_ID"),
}
_PROVIDER_FILES = {
    "vercel": ("vercel.json",),
    "render": ("render.yaml",),
    "railway": ("railway.toml", "railway.json"),
    "replit": (".replit", "replit.nix"),
    "codespaces": (".devcontainer/devcontainer.json",),
}
_DEPLOY_ENV = {
    "vercel": ("VERCEL_TOKEN",),
    "render": ("RENDER_API_KEY", "RENDER_SERVICE_ID"),
    "railway": ("RAILWAY_TOKEN",),
}
_MAX_RESOURCE_BYTES = 2**63 - 1


def _safe_bytes(value: Any) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if 0 <= number <= _MAX_RESOURCE_BYTES else None


def _memory_limit_bytes() -> int | None:
    """Read common Linux cgroup limits without assuming the host exposes them."""
    candidates = (
        Path("/sys/fs/cgroup/memory.max"),
        Path("/sys/fs/cgroup/memory/memory.limit_in_bytes"),
    )
    for path in candidates:
        try:
            raw = path.read_text(encoding="ascii").strip()
        except (OSError, UnicodeError):
            continue
        if raw == "max":
            continue
        value = _safe_bytes(raw)
        # Some cgroup v1 hosts use a huge sentinel to mean unlimited.
        if value is not None and value < 2**60:
            return value
    return None


def _provider(root: Path, env_names: set[str]) -> tuple[str, list[str]]:
    evidence: list[str] = []
    for provider, markers in _PROVIDER_ENV.items():
        matched = sorted(set(markers) & env_names)
        if matched:
            return provider, ["environment_variable_names:" + ",".join(matched)]
    try:
        markers = {item.name for item in root.iterdir() if item.is_file() or item.is_dir()}
    except OSError:
        markers = set()
    for provider, filenames in _PROVIDER_FILES.items():
        matched = sorted(set(filenames) & markers)
        if matched:
            return provider, ["project_markers:" + ",".join(matched)]
    return "generic", evidence


def build_runtime_lifecycle_plan(
    root: str | os.PathLike[str] | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Return a bounded, secret-safe plan for deployment and persistent operation."""
    env = os.environ if environ is None else environ
    env_names = {str(key).upper() for key in env.keys()}
    workspace = Path(root or env.get("NOUS_WORKSPACE_ROOT") or Path.cwd()).expanduser().resolve()
    provider, evidence = _provider(workspace, env_names)

    if provider == "vercel":
        runtime_model = "serverless_or_preview"
        uptime = "request_scoped_or_platform_managed"
        persistence = "external_store_required"
        persistence_detail = "Vercel runtime files are not a durable application database."
    elif provider in {"render", "railway"}:
        runtime_model = "managed_service"
        uptime = "platform_managed_restart_policy"
        volume_name = "RENDER_DISK_PATH" if provider == "render" else "RAILWAY_VOLUME_MOUNT_PATH"
        database_names = {"DATABASE_URL", "POSTGRES_URL", "REDIS_URL"}
        if volume_name in env_names:
            persistence = "persistent_volume_hint"
            persistence_detail = "A volume marker exists; verify the mount and backup policy in the provider dashboard."
        elif database_names & env_names:
            persistence = "external_database_hint"
            persistence_detail = "A database environment-variable name exists; connectivity and durability are not verified."
        else:
            persistence = "unverified"
            persistence_detail = "No recognized persistent-volume or database marker was found."
    elif provider == "replit":
        runtime_model = "hosted_workspace"
        uptime = "deployment_plan_required"
        if "REPLIT_DB_URL" in env_names or {"DATABASE_URL", "POSTGRES_URL"} & env_names:
            persistence = "external_store_hint"
            persistence_detail = "A database marker exists; actual durability and access are not verified."
        else:
            persistence = "unverified"
            persistence_detail = "Workspace files alone are not treated as proof of durable storage."
    elif provider == "codespaces":
        runtime_model = "development_container"
        uptime = "workspace_lifetime_bound"
        persistence = "external_store_required_for_long_lived_state"
        persistence_detail = "Codespace lifetime and storage are tied to workspace policy; use an external store for service continuity."
    elif provider == "lovable":
        runtime_model = "project_authoring_preview"
        uptime = "preview_lifetime_bound"
        persistence = "external_backend_required"
        persistence_detail = "Treat the preview as an authoring surface; run persistent NOUS services on a separately managed backend."
    else:
        runtime_model = "unknown_or_self_hosted"
        uptime = "not_verified"
        if {"DATABASE_URL", "POSTGRES_URL", "REDIS_URL", "NOUS_PERSISTENT_DATA_DIR"} & env_names:
            persistence = "persistence_configuration_hint"
            persistence_detail = "A persistence-related setting exists, but this probe cannot verify durability."
        else:
            persistence = "unverified"
            persistence_detail = "Configure and verify a persistent data store before relying on long-lived memory."

    try:
        disk = shutil.disk_usage(workspace)
        disk_info = {
            "available_bytes": _safe_bytes(disk.free),
            "total_bytes": _safe_bytes(disk.total),
            "workspace_accessible": True,
        }
    except OSError:
        disk_info = {"available_bytes": None, "total_bytes": None, "workspace_accessible": False}

    cpu_count = os.cpu_count()
    memory_limit = _memory_limit_bytes()
    resource_budget = {
        "logical_cpu_count": cpu_count if isinstance(cpu_count, int) and cpu_count > 0 else None,
        "container_memory_limit_bytes": memory_limit,
        "workspace_disk": disk_info,
        "policy": "Use bounded workloads and provider quotas; never consume all available resources.",
    }

    deploy_markers = sorted(set(_DEPLOY_ENV.get(provider, ())) & env_names)
    cli_available = shutil.which(provider) is not None if provider in {"vercel", "railway"} else None
    if provider == "vercel":
        # A CLI installed on the host is not proof that this runtime has deploy
        # access. Only an explicitly present provider credential is a useful hint.
        deploy_ready_hint = "VERCEL_TOKEN" in env_names
    elif provider == "render":
        deploy_ready_hint = {"RENDER_API_KEY", "RENDER_SERVICE_ID"} <= env_names
    elif provider == "railway":
        deploy_ready_hint = cli_available is True or "RAILWAY_TOKEN" in env_names
    else:
        deploy_ready_hint = False

    recommendations: list[dict[str, str]] = []
    if persistence in {"external_store_required", "external_backend_required", "external_store_required_for_long_lived_state", "unverified"}:
        recommendations.append({
            "priority": "high",
            "area": "persistence",
            "action": "Configure a durable database or provider-supported persistent volume and verify a write/read across restart.",
        })
    if provider in {"vercel", "lovable", "codespaces"}:
        recommendations.append({
            "priority": "high",
            "area": "continuous_operation",
            "action": "Run the NOUS control plane on a separately managed always-on service; use this environment for preview and development.",
        })
    if provider in {"vercel", "render", "railway"} and not deploy_ready_hint:
        recommendations.append({
            "priority": "medium",
            "area": "deployment",
            "action": "Configure a narrowly scoped provider integration in the platform secret manager, then test a preview deployment before production.",
        })
    recommendations.append({
        "priority": "medium",
        "area": "recovery",
        "action": "Enable health checks, bounded restart policy, backups, deployment verification, and a tested rollback path.",
    })

    return {
        "ok": True,
        "mode": "read_only_plan",
        "provider": {"id": provider, "evidence": evidence, "access_verified": False},
        "runtime": {"model": runtime_model, "continuity": uptime},
        "persistence": {"status": persistence, "detail": persistence_detail},
        "resources": resource_budget,
        "deployment": {
            "provider_supported_for_direct_deploy": provider in {"vercel", "render"},
            "configured_hint": bool(deploy_ready_hint),
            "credential_variable_names_present": deploy_markers,
            "cli_available": cli_available,
            "automatic_deploy_performed": False,
            "production_deploy_requires_explicit_approval": True,
        },
        "recommendations": recommendations,
        "safety": {
            "environment_values_read": False,
            "secrets_returned": False,
            "filesystem_modified": False,
            "resources_provisioned": False,
            "background_keepalive_started": False,
        },
    }
