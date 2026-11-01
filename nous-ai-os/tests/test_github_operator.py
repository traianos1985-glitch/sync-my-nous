import base64
import json
from unittest.mock import MagicMock, patch
from pathlib import Path
import pytest

from executor import github_operator


def test_status_missing_token(monkeypatch, tmp_path):
    monkeypatch.setattr(github_operator, "CONFIG_PATH", tmp_path / "github_config.json")
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_PAT", raising=False)
    status = github_operator.get_github_status()
    assert status["connected"] is False
    assert status["error"] == "missing_token"


def test_status_connected(monkeypatch, tmp_path):
    monkeypatch.setattr(github_operator, "CONFIG_PATH", tmp_path / "github_config.json")
    github_operator.save_github_config("test-token-123", default_owner="testuser")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "login": "testuser",
        "name": "Test User",
        "avatar_url": "https://avatar.test",
        "html_url": "https://github.com/testuser",
        "public_repos": 5,
        "total_private_repos": 2,
    }
    mock_resp.headers = {
        "X-OAuth-Scopes": "repo, workflow",
        "X-RateLimit-Remaining": "4950",
    }

    with patch("requests.get", return_value=mock_resp):
        status = github_operator.get_github_status()
        assert status["connected"] is True
        assert status["login"] == "testuser"
        assert "repo" in status["scopes"]
        assert status["rate_limit_remaining"] == 4950


def test_list_repositories(monkeypatch, tmp_path):
    monkeypatch.setattr(github_operator, "CONFIG_PATH", tmp_path / "github_config.json")
    github_operator.save_github_config("test-token-123", default_owner="testuser")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {
            "id": 1,
            "name": "my-pages-app",
            "full_name": "testuser/my-pages-app",
            "owner": {"login": "testuser"},
            "html_url": "https://github.com/testuser/my-pages-app",
            "has_pages": True,
            "default_branch": "main",
            "visibility": "public",
            "language": "JavaScript",
        },
        {
            "id": 2,
            "name": "private-tool",
            "full_name": "testuser/private-tool",
            "owner": {"login": "testuser"},
            "html_url": "https://github.com/testuser/private-tool",
            "has_pages": False,
            "default_branch": "main",
            "visibility": "private",
            "language": "Python",
        },
    ]

    with patch("requests.get", return_value=mock_resp):
        res = github_operator.list_repositories()
        assert res["ok"] is True
        assert res["count"] == 2
        assert res["repositories"][0]["has_pages"] is True
        assert res["repositories"][0]["pages_url"] == "https://testuser.github.io/my-pages-app/"
        assert res["repositories"][1]["has_pages"] is False


def test_get_file_content_decodes_base64(monkeypatch, tmp_path):
    monkeypatch.setattr(github_operator, "CONFIG_PATH", tmp_path / "github_config.json")
    
    encoded = base64.b64encode(b"console.log('Hello from GitHub Pages');").decode("utf-8")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "name": "index.js",
        "path": "src/index.js",
        "type": "file",
        "sha": "abc12345",
        "size": 35,
        "content": encoded,
    }

    with patch("requests.get", return_value=mock_resp):
        res = github_operator.get_file_content("testuser", "my-repo", "src/index.js")
        assert res["ok"] is True
        assert res["content"] == "console.log('Hello from GitHub Pages');"
        assert res["sha"] == "abc12345"


def test_commit_file(monkeypatch, tmp_path):
    monkeypatch.setattr(github_operator, "CONFIG_PATH", tmp_path / "github_config.json")
    github_operator.save_github_config("test-token-123")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "commit": {"sha": "sha999", "html_url": "https://github.com/testuser/my-repo/commit/sha999"},
        "content": {"sha": "blob888"},
    }

    with patch("requests.put", return_value=mock_resp):
        res = github_operator.commit_file(
            owner="testuser",
            repo="my-repo",
            path="index.html",
            content="<h1>Updated App</h1>",
            message="feat: upgrade app layout",
            sha="sha-prev",
        )
        assert res["ok"] is True
        assert res["commit_sha"] == "sha999"


def test_deploy_sandbox_app_to_github(monkeypatch, tmp_path):
    monkeypatch.setattr(github_operator, "CONFIG_PATH", tmp_path / "github_config.json")
    github_operator.save_github_config("test-token-123", default_owner="testuser")

    # Create dummy generated app
    apps_dir = tmp_path / "generated_apps"
    demo_app = apps_dir / "quick_calculator"
    demo_app.mkdir(parents=True)
    (demo_app / "index.html").write_text("<h1>Calculator</h1>", encoding="utf-8")
    (demo_app / "app.js").write_text("console.log('calc ready');", encoding="utf-8")

    monkeypatch.setenv("NOUS_DATA_DIR", str(tmp_path))

    with patch("requests.get") as mock_get, patch("requests.post") as mock_post, patch("requests.put") as mock_put:
        # Check repo -> 404 (needs creation)
        mock_check = MagicMock()
        mock_check.status_code = 404

        # Create repo -> 201
        mock_create = MagicMock()
        mock_create.status_code = 201
        mock_create.json.return_value = {
            "name": "quick_calculator",
            "owner": {"login": "testuser"},
            "html_url": "https://github.com/testuser/quick_calculator",
            "default_branch": "main",
        }
        mock_create.text = '{"name": "quick_calculator"}'

        # Commit files -> 200
        mock_commit = MagicMock()
        mock_commit.status_code = 200
        mock_commit.json.return_value = {"commit": {"sha": "c1"}, "content": {"sha": "f1"}}

        # Pages enable -> 201
        mock_pages = MagicMock()
        mock_pages.status_code = 201

        mock_get.return_value = mock_check
        mock_post.side_effect = [mock_create, mock_pages]
        mock_put.return_value = mock_commit

        res = github_operator.deploy_sandbox_app_to_github("quick_calculator")
        assert res["ok"] is True
        assert res["repo_name"] == "quick_calculator"
        assert res["pages_enabled"] is True
        assert "index.html" in res["committed_files"]
        assert "app.js" in res["committed_files"]


def test_github_routes_auth_and_responses(monkeypatch, tmp_path):
    from executor import router
    client = router.app.test_client()

    # 1. Config route requires admin token
    res = client.post("/remote/github/config", json={"token": "t1"})
    assert res.status_code == 401

    # 2. Config with valid token
    monkeypatch.setenv("NOUS_TOKEN", "test-nous-token")
    headers = {"X-NOUS-TOKEN": "test-nous-token"}
    monkeypatch.setattr(github_operator, "CONFIG_PATH", tmp_path / "github_config.json")
    
    res = client.post("/remote/github/config", json={"token": "gh-token-123", "default_owner": "testuser"}, headers=headers)
    assert res.status_code == 200
    assert res.get_json()["ok"] is True

    # 3. Status route
    with patch("executor.github_operator.get_github_status", return_value={"ok": True, "connected": True, "login": "testuser"}):
        res = client.get("/remote/github/status", headers=headers)
        assert res.status_code == 200
        assert res.get_json()["connected"] is True

    # 4. Tree route missing param
    res = client.get("/remote/github/tree", headers=headers)
    assert res.status_code == 400

    # 5. Tree route with params
    with patch("executor.github_operator.get_repository_tree", return_value={"ok": True, "items": [{"name": "index.html"}]}):
        res = client.get("/remote/github/tree?owner=testuser&repo=my-app", headers=headers)
        assert res.status_code == 200
        assert res.get_json()["ok"] is True
