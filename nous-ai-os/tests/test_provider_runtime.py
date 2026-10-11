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
