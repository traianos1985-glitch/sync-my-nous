import json

from executor.preview_preflight import inspect_preview_compatibility


def test_preflight_identifies_javascript_stack_without_returning_scripts(monkeypatch, tmp_path):
    monkeypatch.setenv("NOUS_WORKSPACE_ROOT", str(tmp_path))
    (tmp_path / "package.json").write_text(json.dumps({
        "dependencies": {"next": "15.0.0", "react": "19.0.0"},
        "scripts": {"dev": "next dev --token=never-return-this", "build": "next build"},
    }), encoding="utf-8")
    (tmp_path / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n", encoding="utf-8")

    result = inspect_preview_compatibility()

    assert result["ok"] is True
    assert result["project_types"] == ["node"]
    assert result["detected"]["javascript_lockfiles"] == ["pnpm-lock.yaml"]
    assert result["detected"]["javascript_frameworks"] == ["Next.js", "React"]
    assert result["detected"]["script_names"] == ["build", "dev"]
    assert "never-return-this" not in repr(result)
    providers = {item["id"]: item for item in result["providers"]}
    assert providers["stackblitz"]["recommended"] is True
    assert providers["v0"]["recommended"] is True


def test_preflight_detects_python_framework_by_package_name_only(monkeypatch, tmp_path):
    monkeypatch.setenv("NOUS_WORKSPACE_ROOT", str(tmp_path))
    (tmp_path / "requirements.txt").write_text(
        "fastapi==0.115.0\nuvicorn[standard]>=0.30\n"
        "private-package @ https://user:secret@example.invalid/pkg.whl\n",
        encoding="utf-8",
    )

    result = inspect_preview_compatibility()

    assert result["ok"] is True
    assert result["detected"]["python_frameworks"] == ["FastAPI"]
    assert "secret" not in repr(result)
    assert "example.invalid" not in repr(result)
    assert {item["id"]: item for item in result["providers"]}["railway"]["recommended"] is True


def test_preflight_rejects_workspace_escape(monkeypatch, tmp_path):
    monkeypatch.setenv("NOUS_WORKSPACE_ROOT", str(tmp_path / "workspace"))
    (tmp_path / "workspace").mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()

    result = inspect_preview_compatibility(str(outside))

    assert result == {"ok": False, "error": "project_path_outside_workspace"}


def test_preflight_ignores_manifest_symlink_outside_workspace(monkeypatch, tmp_path):
    import pytest

    monkeypatch.setenv("NOUS_WORKSPACE_ROOT", str(tmp_path / "workspace"))
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    external = tmp_path / "external-package.json"
    external.write_text(json.dumps({"dependencies": {"next": "15"}, "scripts": {"dev": "secret"}}))
    try:
        (workspace / "package.json").symlink_to(external)
    except OSError:
        pytest.skip("symlinks unavailable in this environment")

    result = inspect_preview_compatibility()

    assert result["ok"] is True
    assert result["detected"]["package_json"] is False
    assert result["project_types"] == ["unknown"]
    assert "secret" not in repr(result)
