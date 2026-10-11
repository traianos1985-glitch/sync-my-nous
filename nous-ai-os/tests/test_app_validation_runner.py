from pathlib import Path
from types import SimpleNamespace

from executor import app_validation_runner as runner


def _project(tmp_path: Path, app_name="sample_app"):
    project = tmp_path / app_name
    (project / "tests").mkdir(parents=True)
    (project / "tests" / "test_main.py").write_text(
        "def test_example():\n    assert 2 + 2 == 4\n",
        encoding="utf-8",
    )
    return project


def test_rejects_invalid_app_names_and_timeout_values(tmp_path):
    assert runner.run_project_tests("../outside", tmp_path)["error"] == "invalid_app_name"
    assert runner.run_project_tests("sample_app", tmp_path, 0)["error"] == "timeout_out_of_range"
    assert runner.run_project_tests("sample_app", tmp_path, 301)["error"] == "timeout_out_of_range"


def test_requires_existing_project_and_test_file(tmp_path):
    assert runner.run_project_tests("sample_app", tmp_path)["error"] == "app_not_found"

    project = tmp_path / "sample_app"
    project.mkdir()
    assert runner.run_project_tests("sample_app", tmp_path)["error"] == "automated_tests_not_found"


def test_invokes_pytest_without_shell_and_uses_clean_environment(tmp_path, monkeypatch):
    project = _project(tmp_path)
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return SimpleNamespace(returncode=0, stdout="2 passed", stderr="")

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setenv("API_SECRET", "must-not-leak")
    result = runner.run_project_tests("sample_app", tmp_path, 25)

    assert result["ok"] is True
    assert result["status"] == "passed"
    assert captured["command"][-2:] == ["-q", "tests"]
    assert captured["kwargs"]["shell"] is False
    assert captured["kwargs"]["timeout"] == 25
    assert captured["kwargs"]["cwd"] == str(project.resolve())
    assert "API_SECRET" not in captured["kwargs"]["env"]
    assert result["isolation"]["environment_allowlisted"] is True
    assert result["isolation"]["network_blocked"] is False
    assert result["isolation"]["security_sandbox"] is False


def test_reports_test_failures_and_caps_output(tmp_path, monkeypatch):
    _project(tmp_path)

    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=1,
            stdout="x" * (runner._MAX_OUTPUT_CHARS + 20),
            stderr="assertion failed",
        ),
    )
    result = runner.run_project_tests("sample_app", tmp_path)

    assert result["ok"] is False
    assert result["status"] == "failed"
    assert result["return_code"] == 1
    assert len(result["stdout"]) == runner._MAX_OUTPUT_CHARS
    assert result["output_truncated"] is True


def test_reports_timeout_without_claiming_success(tmp_path, monkeypatch):
    _project(tmp_path)

    def timeout(*args, **kwargs):
        raise runner.subprocess.TimeoutExpired(args[0], kwargs["timeout"], output=b"partial")

    monkeypatch.setattr(runner.subprocess, "run", timeout)
    result = runner.run_project_tests("sample_app", tmp_path, 3)

    assert result["ok"] is False
    assert result["status"] == "timeout"
    assert result["error"] == "test_timeout"
    assert result["timeout_seconds"] == 3
