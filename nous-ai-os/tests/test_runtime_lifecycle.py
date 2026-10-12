from executor.runtime_lifecycle import build_runtime_lifecycle_plan


def test_vercel_preview_is_classified_as_non_durable_and_no_deploy_occurs(tmp_path):
    report = build_runtime_lifecycle_plan(
        tmp_path,
        environ={
            "VERCEL": "1",
            "VERCEL_ENV": "preview",
            "VERCEL_TOKEN": "never-return-this-secret",
            "API_KEY": "also-secret",
        },
    )

    assert report["provider"]["id"] == "vercel"
    assert report["runtime"]["model"] == "serverless_or_preview"
    assert report["persistence"]["status"] == "external_store_required"
    assert report["deployment"]["configured_hint"] is True
    assert report["deployment"]["automatic_deploy_performed"] is False
    assert report["safety"]["filesystem_modified"] is False
    assert "never-return-this-secret" not in repr(report)
    assert "also-secret" not in repr(report)
    assert "VERCEL_TOKEN" in report["deployment"]["credential_variable_names_present"]


def test_render_persistent_disk_is_only_a_hint_until_verified(tmp_path):
    report = build_runtime_lifecycle_plan(
        tmp_path,
        environ={"RENDER": "true", "RENDER_DISK_PATH": "/var/data"},
    )

    assert report["provider"]["id"] == "render"
    assert report["persistence"]["status"] == "persistent_volume_hint"
    assert "verify" in report["persistence"]["detail"].lower()
    assert report["deployment"]["configured_hint"] is False


def test_provider_detection_uses_marker_files_without_claiming_access(tmp_path):
    (tmp_path / "vercel.json").write_text("{}", encoding="utf-8")
    report = build_runtime_lifecycle_plan(tmp_path, environ={})

    assert report["provider"]["id"] == "vercel"
    assert report["provider"]["access_verified"] is False
    assert report["deployment"]["configured_hint"] is False


def test_unknown_environment_returns_bounded_resource_and_recovery_plan(tmp_path):
    report = build_runtime_lifecycle_plan(tmp_path, environ={"PRIVATE_TOKEN": "do-not-leak"})

    assert report["ok"] is True
    assert report["provider"]["id"] == "generic"
    assert report["resources"]["logical_cpu_count"] is None or report["resources"]["logical_cpu_count"] > 0
    assert report["resources"]["workspace_disk"]["workspace_accessible"] is True
    assert any(item["area"] == "recovery" for item in report["recommendations"])
    assert "do-not-leak" not in repr(report)


def test_lifecycle_plan_does_not_create_files_or_start_keepalive(tmp_path):
    before = sorted(path.name for path in tmp_path.iterdir())
    report = build_runtime_lifecycle_plan(tmp_path, environ={"CODESPACES": "true"})
    after = sorted(path.name for path in tmp_path.iterdir())

    assert before == after
    assert report["safety"]["resources_provisioned"] is False
    assert report["safety"]["background_keepalive_started"] is False


def test_lifecycle_endpoint_returns_read_only_plan(monkeypatch):
    from flask import Flask
    from executor import blueprints
    from executor.blueprints import agent_environments_bp

    monkeypatch.setattr(
        agent_environments_bp,
        "build_runtime_lifecycle_plan",
        lambda: {
            "ok": True,
            "mode": "read_only_plan",
            "safety": {"filesystem_modified": False},
        },
    )
    app = Flask("runtime-lifecycle-test")
    app.register_blueprint(agent_environments_bp.agent_environments_bp)
    response = app.test_client().get("/api/agent-environments/lifecycle")

    assert response.status_code == 200
    assert response.get_json()["mode"] == "read_only_plan"
    assert response.get_json()["safety"]["filesystem_modified"] is False
