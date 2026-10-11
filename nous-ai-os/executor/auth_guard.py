"""Global fail-closed authentication and baseline HTTP hardening."""
import threading
import time

from flask import jsonify, request
from executor.security import check_token

PUBLIC_PATHS = {"/", "/health", "/favicon.ico", "/robots.txt"}
PUBLIC_PREFIXES = ("/static/",)
MAX_REQUEST_BYTES = 16 * 1024 * 1024
AUTH_FAILURE_LIMIT = 10
AUTH_FAILURE_WINDOW_SECONDS = 300
AUTH_LOCKOUT_SECONDS = 600
_AUTH_LOCK = threading.Lock()
_AUTH_FAILURES = {}


def is_public(path: str) -> bool:
    return path in PUBLIC_PATHS or path.startswith(PUBLIC_PREFIXES)


def _auth_state(client_ip: str):
    now = time.monotonic()
    with _AUTH_LOCK:
        state = _AUTH_FAILURES.get(client_ip)
        if not state:
            return 0, 0.0
        blocked_until = state["blocked_until"]
        if blocked_until > now:
            return len(state["failures"]), blocked_until
        failures = [stamp for stamp in state["failures"]
                    if now - stamp < AUTH_FAILURE_WINDOW_SECONDS]
        if failures:
            state["failures"] = failures
            state["blocked_until"] = 0.0
            return len(failures), 0.0
        _AUTH_FAILURES.pop(client_ip, None)
        return 0, 0.0


def _record_auth_failure(client_ip: str):
    now = time.monotonic()
    with _AUTH_LOCK:
        state = _AUTH_FAILURES.setdefault(client_ip, {"failures": [], "blocked_until": 0.0})
        if state["blocked_until"] > now:
            return state["blocked_until"]
        state["failures"] = [
            stamp for stamp in state["failures"]
            if now - stamp < AUTH_FAILURE_WINDOW_SECONDS
        ]
        state["failures"].append(now)
        if len(state["failures"]) >= AUTH_FAILURE_LIMIT:
            state["blocked_until"] = now + AUTH_LOCKOUT_SECONDS
        return state["blocked_until"]


def _clear_auth_failures(client_ip: str):
    with _AUTH_LOCK:
        _AUTH_FAILURES.pop(client_ip, None)


def install_auth_guard(app):
    """Install auth, request-size bounds, lockout, and conservative response headers."""
    if app.config.get("MAX_CONTENT_LENGTH") is None:
        app.config["MAX_CONTENT_LENGTH"] = MAX_REQUEST_BYTES

    @app.before_request
    def _nous_auth_guard():
        if request.content_length is not None and request.content_length > app.config["MAX_CONTENT_LENGTH"]:
            return jsonify({"ok": False, "error": "request_too_large"}), 413
        if request.method == "OPTIONS" or is_public(request.path):
            return None
        client_ip = request.remote_addr or "unknown"
        _, blocked_until = _auth_state(client_ip)
        if blocked_until > time.monotonic():
            return jsonify({"ok": False, "error": "auth_rate_limited",
                            "retry_after_seconds": int(blocked_until - time.monotonic()) + 1}), 429
        try:
            authenticated = check_token(request)
        except Exception:
            app.logger.exception("NOUS authentication check failed")
            authenticated = False
        if authenticated:
            _clear_auth_failures(client_ip)
            return None
        blocked_until = _record_auth_failure(client_ip)
        if blocked_until > time.monotonic():
            return jsonify({"ok": False, "error": "auth_rate_limited",
                            "retry_after_seconds": AUTH_LOCKOUT_SECONDS}), 429
        return jsonify({"ok": False, "error": "unauthorized",
                        "hint": "Στείλε X-NOUS-TOKEN ή Authorization: Bearer ..."}), 401

    @app.after_request
    def _nous_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        if request.path.startswith(("/api/", "/remote/", "/token/")):
            response.headers["Cache-Control"] = "no-store"
        if request.is_secure:
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
        return response

    return app
