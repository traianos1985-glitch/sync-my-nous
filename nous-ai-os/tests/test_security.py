"""Smoke tests για το auth μοντέλο (δεν σηκώνουν όλο το router)."""

import importlib

import pytest

flask = pytest.importorskip("flask")


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # data/api_tokens.json σε temp dir
    monkeypatch.delenv("NOUS_TOKEN", raising=False)
    monkeypatch.delenv("NOUS_ALLOW_ANONYMOUS", raising=False)

    import executor.api_tokens as api_tokens
    import executor.auth_guard as auth_guard
    import executor.security as security

    importlib.reload(api_tokens)
    importlib.reload(security)
    importlib.reload(auth_guard)

    application = flask.Flask(__name__)

    @application.route("/health")
    def health():
        return {"ok": True}

    @application.route("/remote/secret")
    def secret():
        return {"ok": True, "secret": True}

    @application.route("/remote/upload", methods=["POST"])
    def upload():
        return {"ok": True}

    auth_guard.install_auth_guard(application)
    return application


def test_health_is_public(app):
    assert app.test_client().get("/health").status_code == 200


def test_local_request_allowed_without_token(app):
    res = app.test_client().get("/remote/secret")
    assert res.status_code == 200


def test_remote_request_rejected_without_token(app):
    res = app.test_client().get("/remote/secret", environ_overrides={"REMOTE_ADDR": "8.8.8.8"})
    assert res.status_code == 401
    assert res.get_json()["error"] == "unauthorized"


def test_env_token_required_when_set(app, monkeypatch):
    monkeypatch.setenv("NOUS_TOKEN", "super-secret-token")
    client = app.test_client()

    assert client.get("/remote/secret").status_code == 401
    assert client.get("/remote/secret", headers={"X-NOUS-TOKEN": "wrong"}).status_code == 401
    assert client.get("/remote/secret", headers={"X-NOUS-TOKEN": "super-secret-token"}).status_code == 200
    assert client.get(
        "/remote/secret", headers={"Authorization": "Bearer super-secret-token"}
    ).status_code == 200


def test_created_api_token_is_accepted(app):
    from executor.api_tokens import create_token, revoke_token

    created = create_token("test")
    client = app.test_client()
    headers = {"X-NOUS-TOKEN": created["token"]}

    res = client.get("/remote/secret", headers=headers, environ_overrides={"REMOTE_ADDR": "8.8.8.8"})
    assert res.status_code == 200

    revoke_token(created["id"])
    res = client.get("/remote/secret", headers=headers, environ_overrides={"REMOTE_ADDR": "8.8.8.8"})
    assert res.status_code == 401


def test_tokens_are_hashed_at_rest(app):
    import json
    import os

    from executor.api_tokens import create_token

    created = create_token("hash-check")
    raw = json.load(open(os.path.join("data", "api_tokens.json"), encoding="utf-8"))
    assert all(created["token"] not in json.dumps(item) for item in raw)


def test_corrupt_token_store_fails_closed_and_is_not_overwritten(app, tmp_path, monkeypatch):
    from executor import api_tokens

    token_file = tmp_path / "data" / "api_tokens.json"
    token_file.parent.mkdir(parents=True, exist_ok=True)
    original = b'{"truncated":'
    token_file.write_bytes(original)
    monkeypatch.setenv("NOUS_ALLOW_ANONYMOUS", "1")
    response = app.test_client().get("/remote/secret", environ_overrides={"REMOTE_ADDR": "8.8.8.8"})
    assert response.status_code == 401
    assert token_file.read_bytes() == original
    with pytest.raises(RuntimeError, match="api_token_store_corrupt"):
        api_tokens.create_token("must not overwrite")
    assert token_file.read_bytes() == original


def test_authenticated_responses_have_security_headers_and_no_store(app, monkeypatch):
    monkeypatch.setenv("NOUS_TOKEN", "safe-test-token")
    response = app.test_client().get("/remote/secret", headers={"X-NOUS-TOKEN": "safe-test-token"})
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["Cache-Control"] == "no-store"


def test_oversized_request_is_rejected(app, monkeypatch):
    monkeypatch.setenv("NOUS_TOKEN", "safe-test-token")
    response = app.test_client().post(
        "/remote/upload", data=b"x" * (16 * 1024 * 1024 + 1),
        headers={"X-NOUS-TOKEN": "safe-test-token", "Content-Type": "application/octet-stream"},
    )
    assert response.status_code == 413


def test_concurrent_token_creation_preserves_every_token(app):
    from concurrent.futures import ThreadPoolExecutor
    from executor import api_tokens

    with ThreadPoolExecutor(max_workers=8) as pool:
        created = list(pool.map(lambda index: api_tokens.create_token(f"worker-{index}"), range(20)))

    assert len({item["id"] for item in created}) == 20
    assert len({item["token"] for item in created}) == 20
    assert api_tokens.token_stats()["active"] == 20
    assert all(api_tokens.token_allowed(item["token"]) for item in created)
