"""Authenticated API for environment inventory, provider probes, and confirmed deployments."""
import hmac
import json
import os

from flask import Blueprint, jsonify, request

from executor.security import check_admin_token

from executor.preview_preflight import inspect_preview_compatibility
from executor.provider_runtime import deploy_provider, probe_provider, provider_inventory, preview_catalog
from executor.runtime_lifecycle import build_runtime_lifecycle_plan
from executor.fleet_coordinator import fleet_auth_configuration, fleet_status, record_heartbeat
from executor.fleet_agent import send_heartbeat
from executor.fleet_rollout import (
    fleet_integration_status, reconcile_and_dispatch, rollout_preflight, rollout_status,
)

agent_environments_bp = Blueprint("agent_environments", __name__, url_prefix="/api/agent-environments")


def _json_object():
    """Accept only JSON objects for mutation/probe endpoints; reject arrays/scalars."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


@agent_environments_bp.get("")
def inventory():
    return jsonify(provider_inventory())


@agent_environments_bp.get("/lifecycle")
def lifecycle():
    """Return a read-only persistence, resource-budget, and deployment readiness plan."""
    return jsonify(build_runtime_lifecycle_plan())


@agent_environments_bp.post("/probe")
def probe():
    data = _json_object()
    if data is None:
        return jsonify({"ok": False, "error": "json_object_required"}), 400
    result = probe_provider(str(data.get("provider") or "").strip())
    return jsonify(result), (200 if result.get("ok") else 400)


@agent_environments_bp.post("/deploy")
def deploy():
    if not check_admin_token(request):
        return jsonify({"ok": False, "error": "admin_scope_required"}), 403
    data = _json_object()
    if data is None:
        return jsonify({"ok": False, "error": "json_object_required"}), 400
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
    """Return launch links enriched with a read-only compatibility estimate for the current workspace."""
    catalog = preview_catalog()
    preflight_result = inspect_preview_compatibility(".")
    catalog["preflight_ok"] = bool(preflight_result.get("ok"))
    if preflight_result.get("ok"):
        fits = {item["id"]: item for item in preflight_result.get("providers", [])}
        for item in catalog.get("previews", []):
            fit = fits.get(item.get("id"))
            if not fit:
                continue
            item["compatibility"] = {
                "fit": fit.get("fit", "unknown"),
                "recommended": bool(fit.get("recommended")),
                "reasons": fit.get("reasons", []),
            }
            status = "Καλή αντιστοίχιση" if fit.get("fit") == "good" else "Χρειάζεται έλεγχο"
            item["description"] = (str(item.get("description") or "").rstrip() +
                                   f" · Preflight: {status}.")
        catalog["preflight"] = {
            "project_types": preflight_result.get("project_types", []),
            "detected": preflight_result.get("detected", {}),
            "limitations": preflight_result.get("limitations", []),
        }
    return jsonify(catalog)


@agent_environments_bp.post("/preflight")
def preflight():
    """Read-only compatibility check; never installs, builds, or provisions a sandbox."""
    data = _json_object()
    if data is None:
        return jsonify({"ok": False, "error": "json_object_required"}), 400
    result = inspect_preview_compatibility(str(data.get("project_path") or "."))
    return jsonify(result), (200 if result.get("ok") else 400)


# Fleet coordination routes live on this already-registered blueprint so existing
# backend deployments gain the API without requiring a separate app bootstrap change.

@agent_environments_bp.after_app_request
def _fleet_heartbeat_after_response(response):
    """Report metadata after a response so 5xx failures can mark an instance degraded."""
    if request.path.startswith("/api/agent-environments/fleet/"):
        return response
    try:
        status = "degraded" if response.status_code >= 500 else "healthy"
        send_heartbeat(status=status)
    except Exception:
        # Fleet telemetry must never break normal NOUS requests.
        pass
    return response



def _fleet_token_matches(payload):
    supplied = request.headers.get("X-NOUS-FLEET-TOKEN", "").strip()
    if not supplied:
        authorization = request.headers.get("Authorization", "")
        if authorization.lower().startswith("bearer "):
            supplied = authorization[7:].strip()
    if not supplied or not isinstance(payload, dict):
        return False
    auth = fleet_auth_configuration()
    if auth["mode"] == "per_instance":
        try:
            mapping = json.loads(os.environ["NOUS_FLEET_INSTANCE_TOKENS"])
        except (KeyError, TypeError, ValueError):
            return False
        expected = mapping.get(str(payload.get("instance_id") or "").strip())
        return bool(isinstance(expected, str) and hmac.compare_digest(expected, supplied))
    if auth["mode"] != "legacy_shared":
        return False
    expected = os.environ.get("NOUS_FLEET_TOKEN", "").strip()
    return bool(expected and hmac.compare_digest(expected, supplied))


@agent_environments_bp.post("/fleet/heartbeat")
def fleet_heartbeat():
    """Record minimal instance metadata using a server-side fleet-only secret."""
    payload = _json_object()
    if payload is None:
        return jsonify({"ok": False, "error": "json_object_required"}), 400
    if not _fleet_token_matches(payload):
        return jsonify({"ok": False, "error": "fleet_authentication_required"}), 403
    result = record_heartbeat(payload)
    return jsonify(result), (200 if result.get("ok") else 400)


@agent_environments_bp.get("/fleet/integrations")
def fleet_integrations_endpoint():
    """Return secret-safe platform delivery paths and coordinator readiness."""
    if not check_admin_token(request):
        return jsonify({"ok": False, "error": "admin_scope_required"}), 403
    return jsonify(fleet_integration_status())


@agent_environments_bp.get("/fleet/status")
def fleet_status_endpoint():
    """Expose fleet status only to an admin-scoped NOUS token."""
    if not check_admin_token(request):
        return jsonify({"ok": False, "error": "admin_scope_required"}), 403
    return jsonify(fleet_status())



def _fleet_rollout_token_matches():
    expected = os.environ.get("NOUS_FLEET_ROLLOUT_TOKEN", "").strip()
    supplied = request.headers.get("X-NOUS-FLEET-ROLLOUT-TOKEN", "").strip()
    return bool(expected and supplied and hmac.compare_digest(expected, supplied))


@agent_environments_bp.get("/fleet/rollout/preflight")
def fleet_rollout_preflight_endpoint():
    """Expose a secret-safe rollout readiness checklist to an administrator."""
    if not check_admin_token(request):
        return jsonify({"ok": False, "error": "admin_scope_required"}), 403
    return jsonify(rollout_preflight())


@agent_environments_bp.get("/fleet/rollout/status")
def fleet_rollout_status_endpoint():
    """Expose bounded rollout job metadata to an administrator."""
    if not check_admin_token(request):
        return jsonify({"ok": False, "error": "admin_scope_required"}), 403
    return jsonify(rollout_status())


@agent_environments_bp.post("/fleet/rollout/reconcile")
def fleet_rollout_reconcile_endpoint():
    """Queue reported drift and dispatch at most one explicitly mapped deployment."""
    if not check_admin_token(request) and not _fleet_rollout_token_matches():
        return jsonify({"ok": False, "error": "rollout_authentication_required"}), 403
    result = reconcile_and_dispatch()
    return jsonify(result), (200 if result.get("ok") else 400)
