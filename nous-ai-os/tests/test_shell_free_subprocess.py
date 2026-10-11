from types import SimpleNamespace

from executor import background_watchdog, code_assistant, larmor_bridge, local_llm_adapter


def test_code_health_commands_do_not_use_a_shell(monkeypatch):
    captured = {}

    def fake_run(argv, **kwargs):
        captured["argv"] = argv
        captured.update(kwargs)
        return SimpleNamespace(returncode=0, stdout="clean\n", stderr="")

    monkeypatch.setattr(code_assistant.subprocess, "run", fake_run)

    result = code_assistant.run_cmd("git status --short")

    assert result["ok"] is True
    assert captured["argv"] == ["git", "status", "--short"]
    assert captured["shell"] is False


def test_local_model_command_does_not_use_a_shell(monkeypatch):
    captured = {}

    def fake_run(argv, **kwargs):
        captured["argv"] = argv
        captured.update(kwargs)
        return SimpleNamespace(returncode=0, stdout="response", stderr="")

    monkeypatch.setitem(local_llm_adapter.CONFIG, "enabled", True)
    monkeypatch.setitem(local_llm_adapter.CONFIG, "command", "ollama run model")
    monkeypatch.setattr(local_llm_adapter.subprocess, "run", fake_run)
    monkeypatch.setattr(local_llm_adapter, "save", lambda *_args, **_kwargs: None)

    result = local_llm_adapter.ask_local("hello")

    assert result["ok"] is True
    assert captured["argv"] == ["ollama", "run", "model"]
    assert captured["shell"] is False


def test_watchdog_git_checks_do_not_use_a_shell(monkeypatch):
    captured = []

    def fake_run(argv, **kwargs):
        captured.append((argv, kwargs))
        output = "main\n" if argv[1] == "rev-parse" else ""
        return SimpleNamespace(returncode=0, stdout=output, stderr="")

    monkeypatch.setattr(background_watchdog.subprocess, "run", fake_run)

    result = background_watchdog.BackgroundWatchdog().check_git_health()

    assert result["branch"] == "main"
    assert result["clean"] is True
    assert [argv for argv, _ in captured] == [
        ["git", "status", "--porcelain"],
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
    ]
    assert all(kwargs["shell"] is False for _, kwargs in captured)


def test_larmor_health_check_keeps_tls_verification_enabled(monkeypatch):
    captured = {}

    def fake_get(url, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(status_code=200, text="Larmor application")

    monkeypatch.setattr(larmor_bridge.requests, "get", fake_get)

    result = larmor_bridge.ping_larmor_app()

    assert result["online"] is True
    assert captured.get("verify", True) is True
