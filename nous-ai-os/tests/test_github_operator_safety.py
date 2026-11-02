"""Safety tests for the GitHub & Pages operator.

No test talks to the real GitHub API: every network call is mocked, and the
tests assert that tokens never appear in responses or logs.
"""
import json
import logging
import os
from unittest.mock import MagicMock, patch

import pytest
import requests

from executor import github_operator

FAKE_TOKEN = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"
NOUS_TOKEN = "test-nous-token-safety"


@pytest.fixture(autouse=True)
def isolated(monkeypatch, tmp_path):
    monkeypatch.setattr(github_operator, "CONFIG_PATH", tmp_path / "github_config.json")
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_PAT", raising=False)
    monkeypatch.setenv("GITHUB_OWNER", "testuser")
    monkeypatch.setenv("NOUS_DATA_DIR", str(tmp_path))
    return tmp_path


def _no_network():
    boom = AssertionError("network must not be used")
    return (
        patch("requests.get", side_effect=boom),
        patch("requests.post", side_effect=boom),
        patch("requests.put", side_effect=boom),
    )


def _make_app(root, name="demo_app"):
    app = root / "generated_apps" / name
    app.mkdir(parents=True)
    (app / "index.html").write_text("<h1>Demo</h1>", encoding="utf-8")
    (app / "app.js").write_text("fetch('/x', {headers: {Authorization: `Bearer ${t}`}})", encoding="utf-8")
    (app / ".env").write_text("GITHUB_TOKEN=abc", encoding="utf-8")
    (app / "key.pem").write_text("-----BEGIN-----", encoding="utf-8")
    (app / "leak.js").write_text(f"const t = '{FAKE_TOKEN}';", encoding="utf-8")
    (app / "node_modules").mkdir()
    (app / "node_modules" / "x.js").write_text("x", encoding="utf-8")
    return app


# ── Missing token ────────────────────────────────────────────────────────────

def test_status_without_token_reports_not_configured():
    status = github_operator.get_github_status()
    assert status["connected"] is False
    assert status["token_configured"] is False
    assert status["token_source"] is None
    assert status["error"] == "missing_token"


@pytest.mark.parametrize("call", [
    lambda: github_operator.commit_file("o", "r", "a.txt", "x", "m"),
    lambda: github_operator.create_or_update_pages_app("repo", {"index.html": "x"}),
])
def test_write_actions_without_token_never_touch_network(call):
    g, p, u = _no_network()
    with g, p, u:
        res = call()
    assert res["ok"] is False
    assert res["error"] == "missing_token"
    assert res["token_required"] is True


def test_sandbox_deploy_without_token_never_touches_network(isolated):
    _make_app(isolated)
    g, p, u = _no_network()
    with g, p, u:
        res = github_operator.deploy_sandbox_app_to_github("demo_app")
    assert res["error"] == "missing_token"


# ── Dry run (safe preview) ───────────────────────────────────────────────────

def test_dry_run_lists_publishable_files_and_excludes_secrets(isolated):
    _make_app(isolated)
    g, p, u = _no_network()
    with g, p, u:
        res = github_operator.deploy_sandbox_app_to_github("demo_app", dry_run=True)
    assert res["ok"] is True and res["dry_run"] is True
    assert res["token_configured"] is False and res["ready"] is False
    assert res["files"] == ["app.js", "index.html"]
    reasons = {e["path"]: e["reason"] for e in res["excluded_files"]}
    assert reasons[".env"] == "sensitive"
    assert reasons["key.pem"] == "sensitive"
    assert reasons["leak.js"] == "contains_credentials"
    assert reasons["node_modules/x.js"] == "sensitive"
    assert FAKE_TOKEN not in json.dumps(res)


def test_dry_run_ready_when_token_configured(isolated):
    _make_app(isolated)
    github_operator.save_github_config(FAKE_TOKEN)
    res = github_operator.deploy_sandbox_app_to_github("demo_app", repo_name="my site", dry_run=True)
    assert res["ready"] is True
    assert res["repo_name"] == "my-site"
    assert res["pages_url"] == "https://testuser.github.io/my-site/"
    assert FAKE_TOKEN not in json.dumps(res)


@pytest.mark.parametrize("name", ["../etc", "..", "a/b", "", "/abs"])
def test_sandbox_app_name_cannot_escape_apps_directory(name):
    res = github_operator.collect_sandbox_app_files(name)
    assert res["ok"] is False
    assert res["error"] in {"invalid_app_name", "path_outside_apps_directory"}


def test_symlinked_files_are_not_published(isolated):
    app = _make_app(isolated)
    outside = isolated / "outside.txt"
    outside.write_text("private", encoding="utf-8")
    os.symlink(outside, app / "link.txt")
    res = github_operator.collect_sandbox_app_files("demo_app")
    assert "link.txt" not in res["files"]
    assert {"path": "link.txt", "reason": "symlink"} in res["excluded_files"]


@pytest.mark.parametrize("path, error", [
    ("../x.html", "unsafe_file_path"),
    ("/etc/passwd", "unsafe_file_path"),
    (".env", "sensitive_file_blocked"),
    ("conf/github_config.json", "sensitive_file_blocked"),
])
def test_pages_app_rejects_unsafe_paths_before_network(path, error):
    github_operator.save_github_config(FAKE_TOKEN)
    g, p, u = _no_network()
    with g, p, u:
        res = github_operator.create_or_update_pages_app("repo", {path: "x"})
    assert res == {**res, "ok": False, "error": error}


# ── Honest results ───────────────────────────────────────────────────────────

def test_partial_commit_failure_is_not_reported_as_success():
    github_operator.save_github_config(FAKE_TOKEN)
    repo = MagicMock(status_code=200)
    repo.json.return_value = {"owner": {"login": "testuser"}, "default_branch": "main", "html_url": "https://github.com/testuser/r"}
    missing = MagicMock(status_code=404)
    ok_put = MagicMock(status_code=201, text="{}")
    ok_put.json.return_value = {"commit": {"sha": "c1"}, "content": {"sha": "f1"}}
    bad_put = MagicMock(status_code=422, text="{}")
    bad_put.json.return_value = {"message": "Invalid request"}
    pages = MagicMock(status_code=201)
    with patch("requests.get", side_effect=[repo, missing, missing]), \
         patch("requests.put", side_effect=[ok_put, bad_put]), \
         patch("requests.post", return_value=pages):
        res = github_operator.create_or_update_pages_app("r", {"a.html": "a", "b.html": "b"})
    assert res["ok"] is False
    assert res["partial"] is True
    assert res["committed_files"] == ["a.html"]
    assert res["failed_files"] == [{"path": "b.html", "error": "Invalid request"}]


def test_pages_enable_failure_is_reported():
    github_operator.save_github_config(FAKE_TOKEN)
    repo = MagicMock(status_code=200)
    repo.json.return_value = {"owner": {"login": "testuser"}, "default_branch": "main"}
    ok_put = MagicMock(status_code=201, text="{}")
    ok_put.json.return_value = {"commit": {"sha": "c1"}, "content": {"sha": "f1"}}
    with patch("requests.get", side_effect=[repo, MagicMock(status_code=404)]), \
         patch("requests.put", return_value=ok_put), \
         patch("requests.post", return_value=MagicMock(status_code=403)):
        res = github_operator.create_or_update_pages_app("r", {"index.html": "a"})
    assert res["ok"] is False
    assert res["pages_enabled"] is False
    assert res["pages_error"] == "github_http_403"


# ── Secrets never leak ───────────────────────────────────────────────────────

def test_status_reports_env_source_without_value(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", FAKE_TOKEN)
    resp = MagicMock(status_code=200, headers={})
    resp.json.return_value = {"login": "testuser"}
    with patch("requests.get", return_value=resp):
        status = github_operator.get_github_status()
    assert status["token_source"] == "env"
    assert FAKE_TOKEN not in json.dumps(status)


def test_network_error_containing_token_is_redacted(caplog):
    github_operator.save_github_config(FAKE_TOKEN)
    exc = requests.ConnectionError(f"failed with Authorization: Bearer {FAKE_TOKEN}")
    with caplog.at_level(logging.DEBUG), patch("requests.get", side_effect=exc), patch("requests.put", side_effect=exc):
        results = [
            github_operator.get_github_status(),
            github_operator.list_repositories(),
            github_operator.get_repository_tree("o", "r"),
            github_operator.get_file_content("o", "r", "a"),
            github_operator.commit_file("o", "r", "a", "x", "m", sha="s"),
        ]
    dumped = json.dumps(results)
    assert FAKE_TOKEN not in dumped
    assert "[REDACTED]" in dumped
    assert FAKE_TOKEN not in caplog.text


def test_github_error_body_echoing_token_is_redacted():
    github_operator.save_github_config(FAKE_TOKEN)
    resp = MagicMock(status_code=401, text="{}")
    resp.json.return_value = {"message": f"Bad credentials {FAKE_TOKEN}"}
    with patch("requests.put", return_value=resp):
        res = github_operator.commit_file("o", "r", "a", "x", "m", sha="s")
    assert FAKE_TOKEN not in res["error"]


def test_redact_secrets_masks_known_and_pattern_tokens():
    text = f"ghp token {FAKE_TOKEN} and github_pat_{'x' * 30} and Bearer abc.def"
    out = github_operator.redact_secrets(text, "")
    assert FAKE_TOKEN not in out and "github_pat_" not in out and "abc.def" not in out
    assert github_operator.redact_secrets({"token": "plain", "safe": "ok"}, "") == {"token": "[REDACTED]", "safe": "ok"}


def test_config_rejects_malformed_token_and_file_is_private(isolated):
    assert github_operator.save_github_config("has space")["error"] == "invalid_token_format"
    assert github_operator.save_github_config(FAKE_TOKEN)["has_token"] is True
    mode = (isolated / "github_config.json").stat().st_mode & 0o777
    assert mode == 0o600


# ── HTTP routes ──────────────────────────────────────────────────────────────

@pytest.fixture
def client(monkeypatch):
    from executor import router
    monkeypatch.setenv("NOUS_TOKEN", NOUS_TOKEN)
    return router.app.test_client()


AUTH = {"X-NOUS-TOKEN": NOUS_TOKEN}


def test_routes_require_nous_token(client):
    for method, path in [
        ("get", "/remote/github/status"),
        ("post", "/remote/github/config"),
        ("post", "/remote/github/commit"),
        ("post", "/remote/github/deploy-pages-app"),
        ("post", "/remote/github/deploy-sandbox-app"),
    ]:
        res = getattr(client, method)(path, json={})
        assert res.status_code == 401, path


def test_route_responses_never_contain_token(client, isolated):
    _make_app(isolated)
    res = client.post("/remote/github/config", json={"token": FAKE_TOKEN}, headers=AUTH)
    assert res.status_code == 200
    assert FAKE_TOKEN not in res.get_data(as_text=True)

    resp = MagicMock(status_code=200, headers={})
    resp.json.return_value = {"login": "testuser"}
    with patch("requests.get", return_value=resp):
        res = client.get("/remote/github/status", headers=AUTH)
    body = res.get_data(as_text=True)
    assert res.get_json()["token_source"] == "config"
    assert FAKE_TOKEN not in body

    res = client.post("/remote/github/deploy-sandbox-app", json={"app_name": "demo_app", "dry_run": True}, headers=AUTH)
    data = res.get_json()
    assert data["dry_run"] is True and data["ready"] is True
    assert FAKE_TOKEN not in res.get_data(as_text=True)


def test_config_route_rejects_bad_token(client):
    res = client.post("/remote/github/config", json={"token": "a b"}, headers=AUTH)
    assert res.status_code == 400


def test_repos_route_tolerates_bad_per_page(client):
    resp = MagicMock(status_code=200)
    resp.json.return_value = []
    with patch("requests.get", return_value=resp) as mocked:
        res = client.get("/remote/github/repos?per_page=abc&sort=evil", headers=AUTH)
    assert res.status_code == 200
    assert res.get_json()["anonymous"] is True
    url = mocked.call_args[0][0]
    assert "per_page=50" in url and "sort=updated" in url


def test_dry_run_route_requires_explicit_true(client, isolated):
    _make_app(isolated)
    res = client.post("/remote/github/deploy-sandbox-app", json={"app_name": "demo_app", "dry_run": "yes"}, headers=AUTH)
    assert res.get_json()["error"] == "missing_token"
