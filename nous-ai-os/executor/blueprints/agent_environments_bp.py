"""Authenticated API for environment inventory, provider probes, and confirmed deployments."""
from flask import Blueprint, jsonify, request

from executor.preview_preflight import inspect_preview_compatibility
from executor.provider_runtime import deploy_provider, probe_provider, provider_inventory, preview_catalog

agent_environments_bp = Blueprint("agent_environments", __name__, url_prefix="/api/agent-environments")


@agent_environments_bp.get("")
def inventory():
    return jsonify(provider_inventory())


@agent_environments_bp.post("/probe")
def probe():
    data = request.get_json(silent=True) or {}
    result = probe_provider(str(data.get("provider") or "").strip())
    return jsonify(result), (200 if result.get("ok") else 400)


@agent_environments_bp.post("/deploy")
def deploy():
    data = request.get_json(silent=True) or {}
    result = deploy_provider(
        provider=data.get("provider"), project_path=data.get("project_path", "."),
        mode=data.get("mode", "preview"), confirmation=data.get("confirmation", ""),
    )
    if result.get("ok"):
        return jsonify(result), 200
    status = 403 if result.get("error") == "explicit_confirmation_required" else 400
    return jsonify(result), status


@agent_environments_bp.get("/previews")
def previews():
    return jsonify(preview_catalog())


@agent_environments_bp.post("/preflight")
def preflight():
    """Read-only compatibility check; never installs, builds, or provisions a sandbox."""
    data = request.get_json(silent=True) or {}
    result = inspect_preview_compatibility(str(data.get("project_path") or "."))
    return jsonify(result), (200 if result.get("ok") else 400)
