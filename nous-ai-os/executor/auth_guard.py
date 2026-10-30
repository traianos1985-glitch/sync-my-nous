"""Global fail-closed authentication and baseline HTTP hardening."""
import os
import threading
import time

from flask import jsonify, request
from werkzeug.middleware.proxy_fix import ProxyFix

from executor.security import check_token, check_admin_token

PUBLIC_PATHS = {"/", "/health", "/favicon.ico", "/robots.txt"}
PUBLIC_PREFIXES = ("/static/",)
ADMIN_ONLY_PREFIXES = (
    "/remote/self-improve/", "/remote/agent/proposals",
    "/api/ops/memory/vector/",
)
ADMIN_ONLY_PATHS = {
    "/api/ops/react/run", "/api/ops/swarm/run", "/api/ops/self-heal/run",
    "/api/ops/watchdog/run", "/api/agent-environments/deploy",
    "/remote/agent/run", "/remote/agent/check",
    "/remote/team/cycle", "/remote/internet-learning/topic",
    "/remote/internet-learning/url", "/remote/master/cycle",
    "/remote/guardian/check", "/remote/technical-intelligence/report",
}
MAX_REQUEST_BYTES = 16 * 1024 * 1024
AUTH_FAILURE_LIMIT = 10
AUTH_FAILURE_WINDOW_SECONDS = 300
AUTH_LOCKOUT_SECONDS = 600
MAX_TRUSTED_PROXY_HOPS = 5
_AUTH_LOCK = threading.Lock()
_AUTH_FAILURES = {}


def _trusted_proxy_hops(app) -> int:
    """Resolve an explicit proxy trust count; Render defaults to its ingress proxy."""
    configured = app.config.get("NOUS_TRUSTED_PROXY_HOPS")
    if configured is None:
        configured = os.environ.get("NOUS_TRUSTED_PROXY_HOPS")
    if configured is None:
        configured = 1 if (
            os.environ.get("RENDER", "").strip().lower() in {"1", "true", "yes", "on"}
            or os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
        ) else 0
    try:
        hops = int(configured)
    except (TypeError, ValueError) as exc:
        raise RuntimeError("NOUS_TRUSTED_PROXY_HOPS must be an integer from 0 to 5") from exc
    if not 0 <= hops <= MAX_TRUSTED_PROXY_HOPS:
        raise RuntimeError("NOUS_TRUSTED_PROXY_HOPS must be an integer from 0 to 5")
    return hops


def is_public(path: str) -> bool:
    return path in PUBLIC_PATHS or path.startswith(PUBLIC_PREFIXES)


def is_admin_only(path: str) -> bool:
    """Central deny-by-default boundary for high-impact operational endpoints."""
    return path in ADMIN_ONLY_PATHS or path.startswith(ADMIN_ONLY_PREFIXES)


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
    """Install trusted-proxy-aware auth, request bounds, lockout, and headers."""
    if app.config.get("MAX_CONTENT_LENGTH") is None:
        app.config["MAX_CONTENT_LENGTH"] = MAX_REQUEST_BYTES

    # request.remote_addr is the reverse proxy address on hosted deployments unless
    # ProxyFix is configured. Trust only the explicitly configured number of hops;
    # never consume X-Forwarded-For directly in the lockout code.
    if not app.config.get("_NOUS_PROXY_FIX_INSTALLED"):
        trusted_hops = _trusted_proxy_hops(app)
        if trusted_hops:
            app.wsgi_app = ProxyFix(app.wsgi_app, x_for=trusted_hops)
        app.config["_NOUS_PROXY_FIX_INSTALLED"] = True

    @app.before_request
    def _nous_auth_guard():
        if request.content_length is not None and request.content_length > app.config["MAX_CONTENT_LENGTH"]:
            return jsonify({"ok": False, "error": "request_too_large"}), 413
        if request.method == "OPTIONS" or is_public(request.path):
            return None

        # After ProxyFix, remote_addr is the client address supplied through the
        # configured trusted proxy chain. In direct mode, untrusted forwarding
        # headers are ignored and the socket peer remains the rate-limit key.
        client_ip = request.remote_addr or "unknown"
        try:
            authenticated = check_token(request)
        except Exception:
            app.logger.exception("NOUS authentication check failed")
            authenticated = False
        if authenticated:
            _clear_auth_failures(client_ip)
            if is_admin_only(request.path):
                try:
                    if not check_admin_token(request):
                        return jsonify({"ok": False, "error": "admin_scope_required"}), 403
                except Exception:
                    app.logger.exception("NOUS admin authorization check failed")
                    return jsonify({"ok": False, "error": "admin_scope_required"}), 403
            return None

        _, blocked_until = _auth_state(client_ip)
        if blocked_until > time.monotonic():
            return jsonify({"ok": False, "error": "auth_rate_limited",
                            "retry_after_seconds": int(blocked_until - time.monotonic()) + 1}), 429

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
