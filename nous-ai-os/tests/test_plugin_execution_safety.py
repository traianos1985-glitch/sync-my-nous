from executor import (\n    code_forge,\n    code_tester,\n    debug_engine,\n    plugin_ai,\n    plugin_builder,\n    plugin_quarantine,\n    plugin_registry,\n)


def test_generated_plugin_validation_never_executes_source(tmp_path):
    marker = tmp_path / "executed.txt"
    source = tmp_path / "generated.py"
    source.write_text(
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('executed')\n"
        "def run():\n"
        "    return {'ok': True}\n",
        encoding="utf-8",
    )

    result = code_forge.test_code(str(source))

    assert result["success"] is True
    assert result["execution_skipped"] is True
    assert result["result"]["validation"] == "static_only"
    assert not marker.exists()


def test_generated_plugin_validation_requires_top_level_run(tmp_path):
    source = tmp_path / "missing_run.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")

    result = code_forge.test_code(str(source))

    assert result == {
        "success": False,
        "error": "missing top-level run() function",
    }
    assert plugin_builder.validate("def not_run():\n    return {}\n") == (
        False,
        "missing top-level run() function",
    )


def test_plugin_ai_generation_does_not_execute_generated_source(tmp_path, monkeypatch):
    marker = tmp_path / "generated-code-executed.txt"
    generated = (
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('executed')\n"
        "def run():\n"
        "    return {'ok': True}\n"
    )
    monkeypatch.setattr(plugin_ai, "ask", lambda _prompt: {"response": generated})
    monkeypatch.setattr(plugin_builder, "PLUGIN_DIR", str(tmp_path))

    result = plugin_ai.generate_plugin("create a simple harmless test plugin")

    assert result["created"]["success"] is True
    assert result["test"]["execution_skipped"] is True
    assert result["test"]["result"]["validation"] == "static_only"
    assert not marker.exists()


def test_plugin_registry_rejects_path_traversal(tmp_path, monkeypatch):
    plugin_dir = tmp_path / "executor" / "plugins"
    plugin_dir.mkdir(parents=True)
    marker = tmp_path / "outside_marker.txt"
    outside = tmp_path / "executor" / "outside.py"
    outside.write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n"
        "def run(): return {'ok': True}\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(plugin_registry, "PLUGIN_DIR", "executor/plugins")

    assert plugin_registry.load_plugin("../outside") is None
    assert plugin_registry.run_plugin("../outside") == {
        "success": False,
        "error": "plugin_not_found",
    }
    assert not marker.exists()


def test_plugin_registry_rejects_symlink_escape(tmp_path, monkeypatch):
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    outside = tmp_path / "outside.py"
    outside.write_text("def run(): return {'ok': True}\n", encoding="utf-8")
    link = plugin_dir / "external.py"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        return
    monkeypatch.setattr(plugin_registry, "PLUGIN_DIR", str(plugin_dir))

    assert plugin_registry.load_plugin("external") is None


def test_quarantine_rejects_path_traversal(tmp_path, monkeypatch):
    plugin_dir = tmp_path / "executor" / "plugins"
    plugin_dir.mkdir(parents=True)
    outside = tmp_path / "executor" / "outside.py"
    outside.write_text("SAFE = True\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = plugin_quarantine.quarantine("../outside")

    assert result == {"success": False, "error": "invalid_plugin_name"}
    assert outside.exists()


def test_legacy_code_tester_never_executes_source(tmp_path):
    marker = tmp_path / "code-tester-executed.txt"
    source = (
        "from pathlib import Path\\n"
        f"Path({str(marker)!r}).write_text('executed')\\n"
        "def run():\\n"
        "    return {'ok': True}\\n"
    )

    result = code_tester.test_plugin(source)

    assert result["success"] is True
    assert result["execution_skipped"] is True
    assert result["result"]["validation"] == "static_only"
    assert not marker.exists()


def test_legacy_debug_engine_never_executes_source(tmp_path):
    marker = tmp_path / "debug-engine-executed.txt"
    source = (
        "from pathlib import Path\\n"
        f"Path({str(marker)!r}).write_text('executed')\\n"
        "VALUE = 42\\n"
    )

    result = debug_engine.run_code(source)

    assert result["execution_skipped"] is True
    assert result["output"]["validation"] == "static_only"
    assert "VALUE" in result["output"]["defined_names"]
    assert not marker.exists()


def test_legacy_code_tester_rejects_source_without_run():
    assert code_tester.test_plugin("VALUE = 1\\n") == {
        "success": False,
        "error": "Missing top-level run() function",
    }
