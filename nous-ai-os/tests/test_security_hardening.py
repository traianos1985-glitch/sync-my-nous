from executor import api_tokens
from executor import android_control
from executor import security


def test_android_open_url_rejects_shell_injection(monkeypatch):
    calls = []
    monkeypatch.setattr(android_control, "_cmd", lambda command: calls.append(command))
    monkeypatch.setattr(android_control, "save", lambda event: None)

    result = android_control.android_open_url('https://x" ; id ; "')

    assert result == {"ok": False, "error": "invalid_http_https_url"}
    assert calls == []


def test_android_open_url_uses_argument_vector_without_shell(monkeypatch):
    calls = []
    monkeypatch.setattr(android_control, "save", lambda event: None)

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        class Result:
            returncode = 0
            stdout = "ok"
            stderr = ""
        return Result()

    monkeypatch.setattr(android_control.subprocess, "run", fake_run)
    result = android_control.android_open_url("https://example.com/path?q=1")

    assert result["ok"] is True
    command, kwargs = calls[0]
    assert command[-1] == "https://example.com/path?q=1"
    assert kwargs["shell"] is False


def test_api_token_scopes_and_legacy_tokens_fail_closed(monkeypatch, tmp_path):
    monkeypatch.setattr(api_tokens, "FILE", str(tmp_path / "api_tokens.json"))
    user = api_tokens.create_token("dashboard", "user")
    admin = api_tokens.create_token("operator", "admin")

    assert api_tokens.token_allowed(user["token"], required_scope="user")
    assert not api_tokens.token_allowed(user["token"], required_scope="admin")
    assert api_tokens.token_allowed(admin["token"], required_scope="user")
    assert api_tokens.token_allowed(admin["token"], required_scope="admin")
    assert api_tokens.list_tokens()[0]["scope"] == "user"


def test_admin_check_accepts_master_or_admin_token_only(monkeypatch, tmp_path):
    monkeypatch.setattr(api_tokens, "FILE", str(tmp_path / "api_tokens.json"))
    user = api_tokens.create_token("dashboard", "user")
    admin = api_tokens.create_token("operator", "admin")
    monkeypatch.setenv("NOUS_TOKEN", "master-secret")

    from flask import Flask
    app = Flask(__name__)
    with app.test_request_context("/", headers={"Authorization": f"Bearer {user['token']}"}):
        assert security.check_token(__import__("flask").request)
        assert not security.check_admin_token(__import__("flask").request)
    with app.test_request_context("/", headers={"Authorization": f"Bearer {admin['token']}"}):
        assert security.check_admin_token(__import__("flask").request)
    with app.test_request_context("/", headers={"Authorization": "Bearer master-secret"}):
        assert security.check_admin_token(__import__("flask").request)


def test_loopback_anonymous_access_denied_when_forwarded_or_tunneled(monkeypatch):
    monkeypatch.delenv("NOUS_TOKEN", raising=False)
    monkeypatch.delenv("NGROK_AUTHTOKEN", raising=False)
    monkeypatch.setattr(security, "_store_has_active_tokens", lambda: False)
    from flask import Flask
    app = Flask(__name__)

    with app.test_request_context("/", environ_base={"REMOTE_ADDR": "127.0.0.1"}):
        assert security.check_token(__import__("flask").request)
    with app.test_request_context("/", headers={"X-Forwarded-For": "127.0.0.1"},
                                 environ_base={"REMOTE_ADDR": "127.0.0.1"}):
        assert not security.check_token(__import__("flask").request)

    monkeypatch.setenv("NGROK_AUTHTOKEN", "configured")
    with app.test_request_context("/", environ_base={"REMOTE_ADDR": "127.0.0.1"}):
        assert not security.check_token(__import__("flask").request)


def test_auth_guard_locks_out_repeated_failures():
    from executor.auth_guard import (
        AUTH_FAILURE_LIMIT,
        _auth_state,
        _clear_auth_failures,
        _record_auth_failure,
    )

    client_ip = "192.0.2.123"
    _clear_auth_failures(client_ip)
    for _ in range(AUTH_FAILURE_LIMIT):
        blocked_until = _record_auth_failure(client_ip)
    assert blocked_until > 0
    _, current_block = _auth_state(client_ip)
    assert current_block > 0
    _clear_auth_failures(client_ip)


def test_public_startup_requires_master_token(monkeypatch):
    import pytest

    monkeypatch.setenv("RENDER", "true")
    monkeypatch.delenv("NOUS_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="NOUS_TOKEN is required"):
        security.validate_startup_security()
