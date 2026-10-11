"""Deployment provider helpers; actual deploys are gated by operator approvals."""
import os
import shutil
import time
from pathlib import Path

from executor.operator_capability_manager import operator_capabilities
from executor.code_assistant import run_cmd
from executor.agent_journal import write_journal


def deploy_provider_status():
    caps = operator_capabilities()
    return {
        "time": time.time(),
        "ready": bool(caps["deploy_ready"]),
        "providers": {
            "vercel": caps["commands"].get("vercel"),
            "railway": caps["commands"].get("railway"),
            "render": caps["commands"].get("render"),
        },
        "install_hints": caps["install_hints"],
    }


def _workspace_root() -> Path:
    configured = os.environ.get("NOUS_WORKSPACE_ROOT", "").strip()
    return Path(configured or Path.cwd()).expanduser().resolve()


def _resolve_project_path(value) -> Path:
    root = _workspace_root()
    raw = str(value or ".").strip()
    if not raw or len(raw) > 1024:
        raise ValueError("invalid_project_path")
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = root / candidate
    try:
        project = candidate.resolve(strict=True)
        project.relative_to(root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ValueError("project_path_outside_workspace_or_missing") from exc
    if not project.is_dir():
        raise ValueError("project_path_not_directory")
    return project


def prepare_provider_deploy(provider, path=".", mode="production"):
    """Validate a deployment request without executing the provider CLI."""
    provider_id = str(provider or "").strip().lower()
    if provider_id not in {"vercel", "railway"}:
        return {"ok": False, "error": "provider_not_supported"}
    mode_value = str(mode or "production").strip().lower()
    if mode_value not in {"production", "preview"}:
        return {"ok": False, "error": "invalid_deployment_mode"}
    if provider_id == "railway" and mode_value != "production":
        return {"ok": False, "error": "preview_deployment_not_supported"}
    try:
        project = _resolve_project_path(path)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    cli = shutil.which(provider_id)
    if not cli:
        return {"ok": False, "error": f"{provider_id}_cli_not_installed"}
    return {
        "ok": True,
        "payload": {
            "provider": provider_id,
            "path": str(project),
            "mode": mode_value,
        },
    }


def execute_provider_deploy(payload):
    """Execute a previously approved, revalidated provider request."""
    if not isinstance(payload, dict):
        return {"ok": False, "error": "invalid_deployment_payload"}
    prepared = prepare_provider_deploy(
        payload.get("provider"), payload.get("path"), payload.get("mode", "production")
    )
    if not prepared.get("ok"):
        return prepared
    provider_id = prepared["payload"]["provider"]
    project = prepared["payload"]["path"]
    cli = shutil.which(provider_id)
    if not cli:
        return {"ok": False, "error": f"{provider_id}_cli_not_installed"}
    mode = prepared["payload"]["mode"]
    if provider_id == "vercel":
        argv = [cli, "--prod", "--yes"] if mode == "production" else [cli, "--yes"]
    else:
        argv = [cli, "up"]
    result = run_cmd(argv, cwd=project, timeout=300)
    output = {
        "ok": bool(result.get("ok")),
        "provider": provider_id,
        "mode": mode,
        "project": Path(project).name or ".",
        "exit_code": result.get("code"),
        "error": result.get("error") if not result.get("ok") else None,
    }
    # Never journal raw CLI stdout/stderr: deployment output can contain secrets.
    write_journal("deploy_provider_run", output)
    return output


def deploy_with_provider(provider, path=".", *, approved=False):
    """Compatibility wrapper that refuses direct, unapproved deployments."""
    if not approved:
        return {"ok": False, "error": "explicit_operator_approval_required"}
    prepared = prepare_provider_deploy(provider, path)
    if not prepared.get("ok"):
        return prepared
    return execute_provider_deploy(prepared["payload"])
