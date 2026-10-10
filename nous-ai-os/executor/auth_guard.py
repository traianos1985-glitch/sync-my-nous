"""Global fail-closed authentication and baseline HTTP hardening."""
from flask import jsonify, request
from executor.security import check_token

PUBLIC_PATHS = {"/", "/health", "/favicon.ico", "/robots.txt"}
PUBLIC_PREFIXES = ("/static/", "/token/")
MAX_REQUEST_BYTES = 16 * 1024 * 1024


def is_public(path: str) -> bool:
    return path in PUBLIC_PATHS or path.startswith(PUBLIC_PREFIXES)


def install_auth_guard(app):
    """Install auth, request-size bounds, and conservative response headers."""
    app.config.setdefault("MAX_CONTENT_LENGTH", MAX_REQUEST_BYTES)

    @app.before_request
    def _nous_auth_guard():
        if request.method == "OPTIONS" or is_public(request.path):
            return None
        try:
            authenticated = check_token(request)
        except Exception:
            app.logger.exception("NOUS authentication check failed")
            authenticated = False
        if authenticated:
            return None
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
