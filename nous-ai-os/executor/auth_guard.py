"""Καθολικό auth guard για το Flask app.

Πριν από αυτό, 216 από τα 351 endpoints δεν έλεγχαν καθόλου token
(π.χ. /read-file, /upload, /remote/tunnel/start, /larmor/inject-*).
Ο guard κλείνει τα πάντα εξ ορισμού και αφήνει ανοιχτά μόνο όσα
είναι όντως δημόσια.
"""

from flask import jsonify, request

from executor.security import check_token

# Δημόσια paths (dashboard + health checks για load balancers)
PUBLIC_PATHS = {
    "/",
    "/health",
    "/favicon.ico",
    "/robots.txt",
}

# Prefixes που κάνουν τον δικό τους (πιο ειδικό) έλεγχο ή είναι static
PUBLIC_PREFIXES = (
    "/static/",
    "/token/",  # χρησιμοποιεί check_admin_token με bootstrap λογική
)


def is_public(path: str) -> bool:
    return path in PUBLIC_PATHS or path.startswith(PUBLIC_PREFIXES)


def install_auth_guard(app):
    """Προσθέτει fail-closed before_request έλεγχο σε όλο το API."""

    @app.before_request
    def _nous_auth_guard():
        if request.method == "OPTIONS":
            return None

        if is_public(request.path):
            return None

        if check_token(request):
            return None

        return (
            jsonify(
                {
                    "ok": False,
                    "error": "unauthorized",
                    "hint": (
                        "Στείλε header X-NOUS-TOKEN (ή Authorization: Bearer ...). "
                        "Τοπικά: όρισε NOUS_TOKEN ή NOUS_ALLOW_ANONYMOUS=1."
                    ),
                }
            ),
            401,
        )

    return app
