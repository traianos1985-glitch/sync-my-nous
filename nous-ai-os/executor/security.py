"""Fail-closed request authentication."""
import os
import secrets

from executor.api_tokens import token_allowed, has_active_tokens

LOOPBACK = {"127.0.0.1", "::1", "localhost", "::ffff:127.0.0.1"}
TRUTHY = {"1", "true", "yes", "on"}
FORWARDED_HEADERS = ("Forwarded", "X-Forwarded-For", "X-Real-IP", "X-Forwarded-Host")


def _env_token():
    return os.environ.get("NOUS_TOKEN", "").strip()


def allow_anonymous():
    return os.environ.get("NOUS_ALLOW_ANONYMOUS", "").strip().lower() in TRUTHY


def admin_token() -> str:
    return _env_token()


def _header_token(request):
    token = request.headers.get("X-NOUS-TOKEN", "")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.lower().startswith("bearer "):
            token = auth[7:]
    return token.strip()


def _has_forwarded_context(request):
    return any(request.headers.get(name) for name in FORWARDED_HEADERS)


def _is_local(request):
    # A loopback REMOTE_ADDR is not sufficient when a proxy supplies the request.
    if _has_forwarded_context(request) or os.environ.get("NGROK_AUTHTOKEN", "").strip():
        return False
    return (getattr(request, "remote_addr", "") or "") in LOOPBACK


def _match_env_token(header_token):
    env_token = _env_token()
    return bool(env_token and header_token and secrets.compare_digest(header_token, env_token))


def _store_has_active_tokens():
    try:
        return has_active_tokens()
    except (OSError, RuntimeError, ValueError, TypeError):
        # A broken token store must never turn into anonymous access.
        return True


def check_token(request):
    """Accept the master NOUS_TOKEN or a non-revoked user/admin API token."""
    header_token = _header_token(request)
    if _match_env_token(header_token):
        return True
    try:
        if header_token and token_allowed(header_token, required_scope="user"):
            return True
    except (OSError, RuntimeError, ValueError, TypeError):
        return False
    if not _env_token() and not _store_has_active_tokens():
        # Explicit anonymous mode is still blocked behind a proxy/public tunnel.
        return _is_local(request) and (allow_anonymous() or _is_local(request))
    return False


def check_admin_token(request):
    """Admin operations require the master token or an explicitly admin-scoped token."""
    header_token = _header_token(request)
    if _match_env_token(header_token):
        return True
    try:
        return bool(header_token and token_allowed(header_token, required_scope="admin"))
    except (OSError, RuntimeError, ValueError, TypeError):
        return False
