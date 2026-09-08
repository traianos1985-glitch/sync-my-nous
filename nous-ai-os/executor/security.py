"""Έλεγχος πρόσβασης (fail-closed).

Παλιά συμπεριφορά: αν δεν υπήρχε NOUS_TOKEN, ΚΑΘΕ request περνούσε — δηλαδή
όλο το API (patch apply, read-file, tunnel, upload) ήταν ανοιχτό στο internet.

Νέα συμπεριφορά:
  * NOUS_TOKEN ορισμένο            -> απαιτείται σωστό token (constant-time)
  * αποθηκευμένο API token         -> επιτρέπεται
  * χωρίς κανένα token configured  -> επιτρέπεται ΜΟΝΟ από localhost,
                                      ή αν NOUS_ALLOW_ANONYMOUS=1
"""

import os
import secrets

from executor.api_tokens import token_allowed, has_active_tokens

LOOPBACK = {"127.0.0.1", "::1", "localhost", "::ffff:127.0.0.1"}
TRUTHY = {"1", "true", "yes", "on"}


def _env_token():
    # διαβάζεται κάθε φορά, ώστε να δουλεύει και μετά από rotate χωρίς restart
    return os.environ.get("NOUS_TOKEN", "").strip()


def allow_anonymous():
    return os.environ.get("NOUS_ALLOW_ANONYMOUS", "").strip().lower() in TRUTHY


def _header_token(request):
    token = request.headers.get("X-NOUS-TOKEN", "")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.lower().startswith("bearer "):
            token = auth[7:]
    return token.strip()


def _is_local(request):
    return (getattr(request, "remote_addr", "") or "") in LOOPBACK


def _match_env_token(header_token):
    env_token = _env_token()
    if not env_token or not header_token:
        return False
    return secrets.compare_digest(header_token, env_token)


def check_token(request):
    header_token = _header_token(request)

    if _match_env_token(header_token):
        return True

    if header_token and token_allowed(header_token):
        return True

    # Κανένα token configured: μόνο τοπική χρήση (ή explicit opt-in).
    if not _env_token() and not has_active_tokens():
        return allow_anonymous() or _is_local(request)

    return False


def check_admin_token(request):
    header_token = _header_token(request)

    if _match_env_token(header_token):
        return True

    if header_token and token_allowed(header_token):
        return True

    # Bootstrap: δημιουργία του πρώτου token επιτρέπεται μόνο τοπικά
    # (ή με explicit NOUS_ALLOW_ANONYMOUS) όσο δεν υπάρχει κανένα token.
    if not _env_token() and not has_active_tokens():
        return allow_anonymous() or _is_local(request)

    return False
