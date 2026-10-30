"""Regression contracts for NOUS's global fail-closed authentication guard."""
from flask import Flask

from executor import auth_guard


def make_app(monkeypatch, *, token_result=False, trusted_proxy_hops=None):
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["MAX_CONTENT_LENGTH"] = 32
    if trusted_proxy_hops is not None:
        app.config["NOUS_TRUSTED_PROXY_HOPS"] = trusted_proxy_hops
    monkeypatch.setattr(auth_guard, "check_token", lambda request: token_result)
    auth_guard.install_auth_guard(app)

    @app.route("/health")
    def health():
        return {"ok": True}

    @app.route("/token/issue")
    def token_issue():
        return {"ok": True}

    @app.route("/remote/status", methods=["GET", "POST"])
    def remote_status():
        return {"ok": True}

    @app.route("/api/payload", methods=["POST"])
    def payload():
        return {"ok": True}

    return app


def test_public_health_and_token_prefix_is_protected(monkeypatch):
    client = make_app(monkeypatch, token_result=False).test_client()

    assert client.get("/health").status_code == 200
    response = client.get("/token/issue")
    assert response.status_code == 401
    assert response.get_json()["error"] == "unauthorized"


def test_token_prefix_allows_authenticated_requests(monkeypatch):
    client = make_app(monkeypatch, token_result=True).test_client()

    assert client.get("/token/issue").status_code == 200


def test_protected_routes_fail_closed_without_valid_token(monkeypatch):
    client = make_app(monkeypatch, token_result=False).test_client()

    for response in (client.get("/remote/status"), client.post("/api/payload", json={"x": 1})):
        assert response.status_code == 401
        assert response.get_json()["error"] == "unauthorized"


def test_protected_routes_allow_authenticated_requests(monkeypatch):
    client = make_app(monkeypatch, token_result=True).test_client()

    assert client.get("/remote/status").status_code == 200
    assert client.post("/api/payload", json={"x": 1}).status_code == 200


def test_authentication_exception_is_denied(monkeypatch):
    app = make_app(monkeypatch)
    monkeypatch.setattr(
        auth_guard,
        "check_token",
        lambda request: (_ for _ in ()).throw(RuntimeError("test failure")),
    )

    response = app.test_client().get("/remote/status")

    assert response.status_code == 401
    assert response.get_json()["error"] == "unauthorized"


def test_options_preflight_is_allowed_without_token(monkeypatch):
    response = make_app(monkeypatch, token_result=False).test_client().options("/remote/status")

    assert response.status_code in (200, 204)


def test_oversized_request_is_rejected_before_authentication(monkeypatch):
    client = make_app(monkeypatch, token_result=False).test_client()

    response = client.post(
        "/api/payload",
        data="x" * 33,
        content_type="text/plain",
    )

    assert response.status_code == 413
    assert response.get_json()["error"] == "request_too_large"


def test_security_headers_and_sensitive_route_cache_policy(monkeypatch):
    response = make_app(monkeypatch, token_result=True).test_client().get("/remote/status")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["Cache-Control"] == "no-store"


def test_public_response_still_receives_baseline_security_headers(monkeypatch):
    response = make_app(monkeypatch, token_result=False).test_client().get("/health")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"


def test_trusted_proxy_uses_forwarded_client_ip_for_independent_lockouts(monkeypatch):
    app = make_app(monkeypatch, token_result=False, trusted_proxy_hops=1)
    client = app.test_client()
    first_ip = "198.51.100.10"
    second_ip = "198.51.100.11"

    first = client.get(
        "/remote/status",
        headers={"X-Forwarded-For": first_ip},
        environ_base={"REMOTE_ADDR": "10.0.0.5"},
    )
    second = client.get(
        "/remote/status",
        headers={"X-Forwarded-For": second_ip},
        environ_base={"REMOTE_ADDR": "10.0.0.5"},
    )

    assert first.status_code == 401
    assert second.status_code == 401
    assert auth_guard._auth_state(first_ip)[0] == 1
    assert auth_guard._auth_state(second_ip)[0] == 1
    assert auth_guard._auth_state("10.0.0.5")[0] == 0

    auth_guard._clear_auth_failures(first_ip)
    auth_guard._clear_auth_failures(second_ip)


def test_direct_mode_ignores_untrusted_forwarded_ip(monkeypatch):
    app = make_app(monkeypatch, token_result=False, trusted_proxy_hops=0)
    client = app.test_client()
    peer_ip = "10.0.0.5"
    spoofed_ip = "198.51.100.99"

    response = client.get(
        "/remote/status",
        headers={"X-Forwarded-For": spoofed_ip},
        environ_base={"REMOTE_ADDR": peer_ip},
    )

    assert response.status_code == 401
    assert auth_guard._auth_state(peer_ip)[0] == 1
    assert auth_guard._auth_state(spoofed_ip)[0] == 0

    auth_guard._clear_auth_failures(peer_ip)


def test_invalid_trusted_proxy_hop_configuration_fails_closed(monkeypatch):
    app = Flask(__name__)
    app.config["NOUS_TRUSTED_PROXY_HOPS"] = 99

    import pytest

    with pytest.raises(RuntimeError, match="NOUS_TRUSTED_PROXY_HOPS"):
        auth_guard.install_auth_guard(app)
