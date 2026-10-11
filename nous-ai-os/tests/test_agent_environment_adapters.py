from executor.agent_environment_adapters import inspect_agent_environment


def test_vercel_detection_uses_names_not_secret_values(tmp_path):
    report = inspect_agent_environment(
        environ={"VERCEL": "1", "VERCEL_URL": "example.invalid", "API_TOKEN": "do-not-return"},
        project_root=tmp_path,
        marker_files=["package.json", "vercel.json"],
    )

    assert report["providers"][0]["id"] == "vercel"
    assert report["providers"][0]["confidence"] == "high"
    assert "VERCEL_URL" in report["providers"][0]["signals"]["environment_variable_names"]
    assert "example.invalid" not in repr(report)
    assert "do-not-return" not in repr(report)
    assert report["security"]["environment_values_read"] is False
    assert report["security"]["external_resources_modified"] is False


def test_lovable_marker_and_generic_fallback(tmp_path):
    lovable = inspect_agent_environment(
        environ={"LOVABLE_PROJECT_ID": "private-id"},
        project_root=tmp_path,
        marker_files=["package.json"],
    )
    generic = inspect_agent_environment(environ={}, project_root=tmp_path, marker_files=[])

    assert any(provider["id"] == "lovable" for provider in lovable["providers"])
    assert generic["providers"][0]["id"] == "generic"


def test_multiple_providers_and_common_project_capabilities():
    report = inspect_agent_environment(
        environ={"REPL_ID": "abc", "RENDER": "true", "NODE": "/usr/bin/node"},
        marker_files=["package.json", "Dockerfile", ".git"],
    )

    ids = {provider["id"] for provider in report["providers"]}
    assert {"replit", "render"} <= ids
    assert {"node_project", "container_build_context", "source_control_metadata"} <= set(report["common_capabilities"])


def test_marker_only_detection_is_not_misreported_as_verified_access():
    report = inspect_agent_environment(
        environ={},
        marker_files=["vercel.json"],
    )

    provider = next(item for item in report["providers"] if item["id"] == "vercel")
    assert provider["confidence"] == "marker_only"
    assert "does not prove" in report["limitations"][0]


def test_environment_input_is_not_mutated():
    env = {"CODESPACES": "true"}
    original = dict(env)

    inspect_agent_environment(environ=env, marker_files=[])

    assert env == original
