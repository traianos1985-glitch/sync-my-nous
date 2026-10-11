from executor import provider_runtime


def test_deploy_requires_exact_confirmation():
    result = provider_runtime.deploy_provider("vercel", confirmation="yes")
    assert result == {"ok": False, "error": "explicit_confirmation_required"}


def test_unknown_provider_cannot_deploy():
    result = provider_runtime.deploy_provider("lovable", confirmation="DEPLOY")
    assert result == {"ok": False, "error": "deployment_not_supported_for_provider"}


def test_project_path_cannot_escape_workspace(monkeypatch, tmp_path):
    monkeypatch.setenv("NOUS_WORKSPACE_ROOT", str(tmp_path))
    outside = tmp_path.parent
    try:
        provider_runtime._resolve_workspace_path(str(outside))
    except ValueError as exc:
        assert str(exc) == "project_path_outside_workspace"
    else:
        raise AssertionError("outside workspace path should be rejected")


def test_inventory_never_returns_secret_values(monkeypatch, tmp_path):
    monkeypatch.setenv("NOUS_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setenv("RENDER_API_KEY", "never-return-this-secret")
    report = provider_runtime.provider_inventory()
    assert "never-return-this-secret" not in repr(report)
    assert "RENDER_API_KEY" not in repr(report["providers"])
    assert report["ok"] is True


def test_render_probe_without_token_does_not_call_network(monkeypatch):
    monkeypatch.delenv("RENDER_API_KEY", raising=False)
    result = provider_runtime._render_request("GET", "/v1/services?limit=1")
    assert result == {"ok": False, "configured": False, "error": "render_api_key_not_configured"}



def test_vercel_api_probe_without_token_does_not_call_network(monkeypatch):
    monkeypatch.delenv("VERCEL_TOKEN", raising=False)
    result = provider_runtime._vercel_api_probe()
    assert result == {"ok": False, "configured": False, "error": "vercel_token_not_configured"}


def test_vercel_api_probe_uses_token_without_returning_it(monkeypatch):
    import json

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, _limit):
            return json.dumps({"projects": [{"id": "project-id"}]}).encode()

    captured = {}

    def fake_urlopen(request, timeout):
        captured["authorization"] = request.get_header("Authorization")
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setenv("VERCEL_TOKEN", "must-not-appear-in-output")
    monkeypatch.setattr(provider_runtime.urllib.request, "urlopen", fake_urlopen)
    result = provider_runtime._vercel_api_probe()
    assert result == {"ok": True, "configured": True, "status_code": 200, "projects_visible": 1}
    assert captured["authorization"] == "Bearer must-not-appear-in-output"
    assert "must-not-appear-in-output" not in repr(result)



def test_github_repo_slug_accepts_https_and_ssh_without_leaking_credentials():
    assert provider_runtime._github_repo_slug("https://github.com/acme/demo.git") == "acme/demo"
    assert provider_runtime._github_repo_slug("git@github.com:acme/demo.git") == "acme/demo"
    assert provider_runtime._github_repo_slug("https://user:secret@github.com/acme/demo.git") is None


def test_github_repo_slug_rejects_non_github_and_malformed_urls():
    assert provider_runtime._github_repo_slug("https://example.com/acme/demo.git") is None
    assert provider_runtime._github_repo_slug("git@github.com:../demo.git") is None


def test_preview_catalog_returns_direct_launch_links_for_github_origin(monkeypatch, tmp_path):
    monkeypatch.setenv("NOUS_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setattr(provider_runtime.shutil, "which", lambda name: "/usr/bin/git" if name == "git" else None)
    monkeypatch.setattr(provider_runtime, "_run_cli", lambda args, cwd, timeout=12: {
        "ok": True, "stdout": "git@github.com:acme/demo.git", "stderr": ""
    })
    result = provider_runtime.preview_catalog()
    assert result["github_repository"] == "https://github.com/acme/demo"
    previews = {item["id"]: item for item in result["previews"]}
    assert previews["stackblitz"]["url"] == "https://stackblitz.com/github/acme/demo"
    assert previews["codesandbox"]["url"] == "https://codesandbox.io/p/sandbox/github/acme/demo"
    assert previews["v0"]["repository_url"] == "https://github.com/acme/demo"
    assert all(item["ready"] for item in result["previews"])


def test_preview_catalog_falls_back_to_provider_homepages_without_github(monkeypatch, tmp_path):
    monkeypatch.setenv("NOUS_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setattr(provider_runtime.shutil, "which", lambda _name: None)
    result = provider_runtime.preview_catalog()
    assert result["github_repository"] is None
    assert all(not item["ready"] for item in result["previews"])
    assert all(item["url"].startswith("https://") for item in result["previews"])


def test_render_preview_mode_is_rejected_before_any_deployment(monkeypatch, tmp_path):
    monkeypatch.setenv("NOUS_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setenv("RENDER_SERVICE_ID", "srv_123")
    monkeypatch.setenv("RENDER_API_KEY", "test-token")
    monkeypatch.setattr(
        provider_runtime,
        "_render_request",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("preview mode must never call the production deploy endpoint")
        ),
    )

    result = provider_runtime.deploy_provider(
        "render", project_path=".", mode="preview", confirmation="DEPLOY"
    )

    assert result == {
        "ok": False,
        "error": "render_preview_deployment_not_supported",
    }


def test_render_production_mode_remains_explicitly_available(monkeypatch, tmp_path):
    monkeypatch.setenv("NOUS_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setenv("RENDER_SERVICE_ID", "srv_123")
    monkeypatch.setenv("RENDER_API_KEY", "test-token")
    calls = []

    def fake_render_request(method, path):
        calls.append((method, path))
        return {"ok": True, "status_code": 201, "data": {"id": "dep_123"}}

    monkeypatch.setattr(provider_runtime, "_render_request", fake_render_request)

    result = provider_runtime.deploy_provider(
        "render", project_path=".", mode="production", confirmation="DEPLOY"
    )

    assert result["ok"] is True
    assert result["mode"] == "production"
    assert result["deployment_id"] == "dep_123"
    assert calls == [("POST", "/v1/services/srv_123/deploys")]


def test_render_preview_rejection_does_not_require_workspace_or_credentials(monkeypatch):
    monkeypatch.delenv("NOUS_WORKSPACE_ROOT", raising=False)
    monkeypatch.delenv("RENDER_SERVICE_ID", raising=False)
    monkeypatch.delenv("RENDER_API_KEY", raising=False)

    result = provider_runtime.deploy_provider(
        "render", mode="preview", confirmation="DEPLOY"
    )

    assert result == {
        "ok": False,
        "error": "render_preview_deployment_not_supported",
    }
