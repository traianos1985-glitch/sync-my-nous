"""Authenticated control-plane endpoints for NOUS installation coordination."""
import hmac
import os

from flask import Blueprint, jsonify, request

from executor.fleet_coordinator import fleet_status, record_heartbeat
from executor.security import check_admin_token

fleet_bp = Blueprint("fleet", __name__, url_prefix="/api/fleet")


def _fleet_token_matches() -> bool:
    expected = os.environ.get("NOUS_FLEET_TOKEN", "").strip()
    supplied = request.headers.get("X-NOUS-FLEET-TOKEN", "").strip()
    if not supplied:
        authorization = request.headers.get("Authorization", "")
        if authorization.lower().startswith("bearer "):
            supplied = authorization[7:].strip()
    return bool(expected and supplied and hmac.compare_digest(expected, supplied))


@fleet_bp.post("/heartbeat")
def heartbeat():
    """Accept minimal metadata from an installation using the fleet-only secret."""
    if not _fleet_token_matches():
        return jsonify({"ok": False, "error": "fleet_authentication_required"}), 403
    payload = request.get_json(silent=True)
    result = record_heartbeat(payload)
    return jsonify(result), (200 if result.get("ok") else 400)


@fleet_bp.get("/status")
def status():
    """Return fleet metadata to an admin; never expose fleet credentials."""
    if not check_admin_token(request):
        return jsonify({"ok": False, "error": "admin_scope_required"}), 403
    return jsonify(fleet_status())
