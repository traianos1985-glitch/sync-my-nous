"""Best-effort, request-driven heartbeat client for a NOUS installation.

No background thread or scheduler is created: this also works on serverless hosts.
It reports only bounded instance/version/health metadata to a configured HTTPS
coordinator. Missing configuration and network failures are intentionally non-fatal.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

_LOCK = threading.Lock()
_LAST_SENT = 0.0
_INTERVAL_SECONDS = 300
_TIMEOUT_SECONDS = 1.5
_INSTANCE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,79}$")


def _provider() -> str:
    if os.environ.get("RENDER_SERVICE_ID") or os.environ.get("RENDER_EXTERNAL_HOSTNAME"):
        return "render"
    if os.environ.get("VERCEL") or os.environ.get("VERCEL_URL"):
        return "vercel"
    if os.environ.get("REPL_ID"):
        return "replit"
    if os.environ.get("CODESPACES") or os.environ.get("CODESPACE_NAME"):
        return "codespaces"
    if os.environ.get("LOVABLE_PROJECT_ID"):
        return "lovable"
    return re.sub(r"[^a-z0-9_-]", "", os.environ.get("NOUS_FLEET_PROVIDER", "generic").lower())[:32] or "generic"


def _version_metadata() -> tuple[str, str]:
    version = (os.environ.get("NOUS_VERSION") or os.environ.get("RENDER_GIT_COMMIT")
               or os.environ.get("VERCEL_GIT_COMMIT_SHA") or os.environ.get("GITHUB_SHA")
               or "unknown").strip()[:120]
    commit = (os.environ.get("RENDER_GIT_COMMIT") or os.environ.get("VERCEL_GIT_COMMIT_SHA")
              or os.environ.get("GITHUB_SHA") or "").strip()
    if not re.fullmatch(r"[A-Fa-f0-9]{7,64}", commit):
        commit = ""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+/-]{0,119}", version):
        version = "unknown"
    return version, commit


def send_heartbeat(force: bool = False) -> dict[str, Any]:
    """Send one bounded HTTPS heartbeat; never includes prompts, user data, or tokens in JSON."""
    global _LAST_SENT
    coordinator = os.environ.get("NOUS_FLEET_COORDINATOR_URL", "").strip().rstrip("/")
    token = os.environ.get("NOUS_FLEET_TOKEN", "").strip()
    instance_id = os.environ.get("NOUS_FLEET_INSTANCE_ID", "").strip()
    if not coordinator or not token or not _INSTANCE_ID.fullmatch(instance_id):
        return {"ok": False, "skipped": True, "reason": "fleet_client_not_configured"}

    parsed = urllib.parse.urlsplit(coordinator)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        return {"ok": False, "skipped": True, "reason": "coordinator_must_be_https"}
    now = time.monotonic()
    with _LOCK:
        if not force and now - _LAST_SENT < _INTERVAL_SECONDS:
            return {"ok": True, "skipped": True, "reason": "heartbeat_interval"}
        _LAST_SENT = now

    version, commit = _version_metadata()
    payload = {
        "instance_id": instance_id,
        "provider": _provider(),
        "version": version,
        "commit_sha": commit,
        "status": "healthy",
    }
    endpoint = coordinator + "/api/agent-environments/fleet/heartbeat"
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json",
                 "X-NOUS-FLEET-TOKEN": token},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
            raw = response.read(8192)
            result = json.loads(raw.decode("utf-8")) if raw else {}
            return {"ok": 200 <= response.status < 300, "coordinator_status": response.status,
                    "desired_version": result.get("desired_version"),
                    "update_available": bool(result.get("update_available"))}
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError):
        return {"ok": False, "error": "coordinator_unreachable"}


def reset_heartbeat_for_tests() -> None:
    """Reset the process-local throttle for tests."""
    global _LAST_SENT
    with _LOCK:
        _LAST_SENT = 0.0
