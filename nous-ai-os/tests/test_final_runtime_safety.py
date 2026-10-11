import importlib
import json
from pathlib import Path

from executor import conversation_manager
from executor import conversation_summary_engine
from executor import plugin_quarantine
from executor import plugin_registry
from executor import runtime_diagnostics


def test_auto_mission_executor_refuses_to_overwrite_corrupt_state(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import executor.auto_mission_executor as executor
    executor = importlib.reload(executor)
    state_path = tmp_path / "data" / "auto_mission_executor.json"
    state_path.parent.mkdir(parents=True)
    original = b'{"enabled":'
    state_path.write_bytes(original)
    monkeypatch.setattr(executor, "FILE", str(state_path))

    enabled = executor.set_auto_mission_executor_enabled(True)
    run = executor.run_auto_mission_executor()
    status = executor.auto_mission_executor_status()

    assert enabled == {"ok": False, "error": "state_load_failed", "enabled": False}
    assert status["state_error"] == "state_load_failed"
    assert run == {"ok": False, "error": "state_load_failed"}
    assert state_path.read_bytes() == original


def test_plugin_registry_rejects_symlink_to_another_plugin(tmp_path, monkeypatch):
    plugins = tmp_path / "plugins"
    plugins.mkdir()
    (plugins / "real.py").write_text("def run(): return 'real'\n", encoding="utf-8")
    alias = plugins / "alias.py"
    try:
        alias.symlink_to(plugins / "real.py")
    except (OSError, NotImplementedError):
        return
    monkeypatch.setattr(plugin_registry, "PLUGIN_DIR", str(plugins))

    assert plugin_registry.load_plugin("alias") is None
    assert "alias" not in plugin_registry.list_plugins()


def test_quarantine_refuses_to_overwrite_existing_artifact(tmp_path, monkeypatch):
    plugins = tmp_path / "plugins"
    quarantine = tmp_path / "quarantine"
    plugins.mkdir()
    quarantine.mkdir()
    source = plugins / "sample.py"
    destination = quarantine / "sample.py"
    source.write_text("SAFE = True\n", encoding="utf-8")
    destination.write_text("PRESERVE THIS\n", encoding="utf-8")
    monkeypatch.setattr(plugin_quarantine, "PLUGIN_DIR", plugins)
    monkeypatch.setattr(plugin_quarantine, "QUARANTINE_DIR", quarantine)

    result = plugin_quarantine.quarantine("sample")

    assert result == {"success": False, "error": "quarantine_destination_exists"}
    assert source.read_text(encoding="utf-8") == "SAFE = True\n"
    assert destination.read_text(encoding="utf-8") == "PRESERVE THIS\n"


def test_quarantine_rejects_symlinked_plugin_even_if_target_is_inside_root(tmp_path, monkeypatch):
    plugins = tmp_path / "plugins"
    quarantine = tmp_path / "quarantine"
    plugins.mkdir()
    (plugins / "real.py").write_text("SAFE = True\n", encoding="utf-8")
    try:
        (plugins / "alias.py").symlink_to(plugins / "real.py")
    except (OSError, NotImplementedError):
        return
    monkeypatch.setattr(plugin_quarantine, "PLUGIN_DIR", plugins)
    monkeypatch.setattr(plugin_quarantine, "QUARANTINE_DIR", quarantine)

    assert plugin_quarantine.quarantine("alias") == {
        "success": False,
        "error": "plugin_not_found",
    }
    assert (plugins / "real.py").exists()


def test_runtime_diagnostics_do_not_expose_exception_messages():
    result = runtime_diagnostics._component(
        "private_component",
        lambda: (_ for _ in ()).throw(RuntimeError("token=private-secret /srv/private/path")),
    )

    assert result == {
        "name": "private_component",
        "status": "unavailable",
        "error": "RuntimeError",
    }
    assert "private-secret" not in json.dumps(result)
    assert "/srv/private/path" not in json.dumps(result)


def test_summary_updates_history_index_and_report_names_are_unique(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    conv_dir = tmp_path / "data" / "conversations"
    index_path = tmp_path / "data" / "conversation_index.json"
    reports = tmp_path / "data" / "reports"
    monkeypatch.setattr(conversation_manager, "CONV_DIR", conv_dir)
    monkeypatch.setattr(conversation_manager, "INDEX", index_path)
    monkeypatch.setattr(conversation_summary_engine, "CONV_DIR", conv_dir)
    monkeypatch.setattr(conversation_summary_engine, "REPORTS", reports)

    created = conversation_manager.append_turn(
        "Ας ελέγξουμε τη σταθερότητα της μνήμης",
        "Καταγράφηκε η δοκιμή",
    )
    conversation_id = created["conversation_id"]

    first = conversation_summary_engine.update_conversation_summary(conversation_id)
    second = conversation_summary_engine.update_conversation_summary(conversation_id)
    saved = conversation_manager.get_conversation(conversation_id)
    index = conversation_manager.list_conversations()["conversations"]

    assert first["ok"] is True and second["ok"] is True
    assert first["report_path"] != second["report_path"]
    assert saved["summary"]
    assert index[0]["id"] == conversation_id
    assert index[0]["updated_at"] == saved["updated_at"]
    assert Path(first["report_path"]).exists()
    assert Path(second["report_path"]).exists()


def test_self_diagnosis_uses_configured_token_for_internal_probes(monkeypatch):
    from executor import self_diagnosis

    monkeypatch.setenv("NOUS_TOKEN", "private-diagnostic-token")
    headers = self_diagnosis._internal_diagnostic_headers()

    assert headers == {"Authorization": "Bearer private-diagnostic-token"}
    assert "private-diagnostic-token" not in json.dumps({"headers_present": bool(headers)})


def test_self_diagnosis_internal_probes_do_not_require_token_in_report(monkeypatch):
    from executor import self_diagnosis

    monkeypatch.delenv("NOUS_TOKEN", raising=False)
    assert self_diagnosis._internal_diagnostic_headers() == {}
