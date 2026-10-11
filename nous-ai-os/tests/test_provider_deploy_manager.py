from executor import deploy_provider_manager as manager


def test_prepare_provider_deploy_rejects_path_escape(monkeypatch, tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    monkeypatch.setenv("NOUS_WORKSPACE_ROOT", str(root))
    monkeypatch.setattr(manager.shutil, "which", lambda _provider: "/usr/bin/vercel")

    result = manager.prepare_provider_deploy("vercel", str(outside))

    assert result == {"ok": False, "error": "project_path_outside_workspace_or_missing"}


def test_prepare_provider_deploy_is_read_only_and_normalizes_payload(monkeypatch, tmp_path):
    root = tmp_path / "workspace"
    project = root / "app"
    project.mkdir(parents=True)
    monkeypatch.setenv("NOUS_WORKSPACE_ROOT", str(root))
    monkeypatch.setattr(manager.shutil, "which", lambda _provider: "/usr/bin/vercel")

    result = manager.prepare_provider_deploy("vercel", "app")

    assert result == {"ok": True, "payload": {"provider": "vercel", "path": str(project.resolve()), "mode": "production"}}


def test_execute_provider_deploy_uses_argv_cwd_and_does_not_return_raw_output(monkeypatch, tmp_path):
    root = tmp_path / "workspace"
    project = root / "app"
    project.mkdir(parents=True)
    monkeypatch.setenv("NOUS_WORKSPACE_ROOT", str(root))
    monkeypatch.setattr(manager.shutil, "which", lambda _provider: "/usr/bin/vercel")
    captured = {}

    def fake_run_cmd(argv, cwd=None, timeout=30):
        captured.update(argv=argv, cwd=cwd, timeout=timeout)
        return {"ok": True, "code": 0, "stdout": "sensitive-output", "stderr": ""}

    monkeypatch.setattr(manager, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(manager, "write_journal", lambda *_args: None)

    result = manager.execute_provider_deploy({"provider": "vercel", "path": str(project)})

    assert result["ok"] is True
    assert captured == {
        "argv": ["/usr/bin/vercel", "--prod", "--yes"],
        "cwd": str(project.resolve()),
        "timeout": 300,
    }
    assert "sensitive-output" not in repr(result)


def test_legacy_deploy_wrapper_refuses_without_approval():
    assert manager.deploy_with_provider("vercel", ".") == {
        "ok": False,
        "error": "explicit_operator_approval_required",
    }



def test_vercel_preview_mode_does_not_add_production_flag(monkeypatch, tmp_path):
    root = tmp_path / "workspace"
    project = root / "app"
    project.mkdir(parents=True)
    monkeypatch.setenv("NOUS_WORKSPACE_ROOT", str(root))
    monkeypatch.setattr(manager.shutil, "which", lambda _provider: "/usr/bin/vercel")
    captured = {}
    monkeypatch.setattr(
        manager,
        "run_cmd",
        lambda argv, cwd=None, timeout=30: captured.update(argv=argv, cwd=cwd, timeout=timeout)
        or {"ok": True, "code": 0, "stdout": "", "stderr": ""},
    )
    monkeypatch.setattr(manager, "write_journal", lambda *_args: None)

    result = manager.execute_provider_deploy({
        "provider": "vercel", "path": str(project), "mode": "preview"
    })

    assert result["ok"] is True
    assert result["mode"] == "preview"
    assert captured["argv"] == ["/usr/bin/vercel", "--yes"]
