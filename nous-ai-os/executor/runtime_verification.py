"""Verify a deployed NOUS service without keeping it awake or changing state.

The verifier is intended for an explicit post-deployment run. It never retries
indefinitely, sends credentials, follows caller-supplied paths, or mutates the
remote service.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlsplit, urlunsplit

_TIMEOUT_SECONDS = 8
_MAX_RESPONSE_BYTES = 64 * 1024
_REQUIRED_ENDPOINTS = ("/api/system/health", "/api/system/ready")


def _base_url(value: str) -> str:
    """Validate an HTTPS origin/base path without credentials or query data."""
    raw = str(value or "").strip()
    try:
        parsed = urlsplit(raw)
        _ = parsed.port  # Force malformed-port validation.
    except ValueError as exc:
        raise ValueError("invalid_healthcheck_url") from exc
    if (
        parsed.scheme.lower() != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("invalid_healthcheck_url")
    path = parsed.path.rstrip("/")
    return urlunsplit(("https", parsed.netloc, path, "", ""))


def _request_json(url: str, opener: Any = urllib.request.urlopen) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "NOUS-runtime-verifier/1.0"},
        method="GET",
    )
    try:
        with opener(request, timeout=_TIMEOUT_SECONDS) as response:
            status_code = int(response.status)
            raw = response.read(_MAX_RESPONSE_BYTES + 1)
        if status_code < 200 or status_code >= 300:
            return {"ok": False, "status_code": status_code, "error": "http_status_not_success"}
        if len(raw) > _MAX_RESPONSE_BYTES:
            return {"ok": False, "status_code": status_code, "error": "response_too_large"}
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            return {"ok": False, "status_code": status_code, "error": "invalid_json_object"}
        return {"ok": True, "status_code": status_code, "payload": payload}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "status_code": int(exc.code), "error": "http_status_not_success"}
    except (urllib.error.URLError, TimeoutError, OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return {"ok": False, "status_code": None, "error": "endpoint_unreachable_or_invalid"}


def verify_runtime(base_url: str, opener: Any = urllib.request.urlopen) -> dict[str, Any]:
    """Perform one bounded liveness and readiness check against a configured HTTPS URL."""
    try:
        base = _base_url(base_url)
    except ValueError:
        return {"ok": False, "error": "invalid_healthcheck_url", "checks": []}

    checks: list[dict[str, Any]] = []
    for endpoint in _REQUIRED_ENDPOINTS:
        result = _request_json(base + endpoint, opener=opener)
        payload = result.pop("payload", {})
        semantic_ok = result.get("ok") is True
        if endpoint.endswith("/health"):
            semantic_ok = semantic_ok and payload.get("status") == "healthy" and payload.get("kind") == "liveness"
        else:
            semantic_ok = semantic_ok and payload.get("ok") is True
        checks.append({"endpoint": endpoint, "ok": bool(semantic_ok),
                       "status_code": result.get("status_code"),
                       "error": result.get("error") if not semantic_ok else None})
    return {"ok": all(item["ok"] for item in checks), "checks": checks,
            "mode": "single_post_deploy_probe", "remote_state_changed": False}


def main() -> int:
    url = os.environ.get("NOUS_HEALTHCHECK_URL", "")
    if not url:
        print(json.dumps({"ok": False, "error": "NOUS_HEALTHCHECK_URL_not_configured"}))
        return 2
    report = verify_runtime(url)
    print(json.dumps(report, sort_keys=True))
    return 0 if report.get("ok") is True else 1


if __name__ == "__main__":
    sys.exit(main())
