from executor import code_forge, plugin_builder


_VALID_PLUGIN = "def run():\n    return {'ok': True}\n"


def test_plugin_builder_refuses_symlink_destination(tmp_path, monkeypatch):
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    outside = tmp_path / "important.txt"
    outside.write_text("keep me", encoding="utf-8")
    link = plugin_dir / "external.py"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        return
    monkeypatch.setattr(plugin_builder, "PLUGIN_DIR", str(plugin_dir))

    result = plugin_builder.create_plugin("external", _VALID_PLUGIN)

    assert result == {"success": False, "error": "plugin_already_exists"}
    assert outside.read_text(encoding="utf-8") == "keep me"


def test_plugin_builder_refuses_path_traversal_names(tmp_path, monkeypatch):
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    monkeypatch.setattr(plugin_builder, "PLUGIN_DIR", str(plugin_dir))

    result = plugin_builder.create_plugin("../outside", _VALID_PLUGIN)

    assert result == {"success": False, "error": "invalid_plugin_name"}
    assert not (tmp_path / "outside.py").exists()


def test_plugin_builder_refuses_overwriting_existing_plugin(tmp_path, monkeypatch):
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    existing = plugin_dir / "existing.py"
    existing.write_text("ORIGINAL = True\n", encoding="utf-8")
    monkeypatch.setattr(plugin_builder, "PLUGIN_DIR", str(plugin_dir))

    result = plugin_builder.create_plugin("existing", _VALID_PLUGIN)

    assert result == {"success": False, "error": "plugin_already_exists"}
    assert existing.read_text(encoding="utf-8") == "ORIGINAL = True\n"


def test_code_forge_cannot_overwrite_symlink_target(tmp_path, monkeypatch):
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    outside = tmp_path / "important.txt"
    outside.write_text("keep me", encoding="utf-8")
    link = plugin_dir / "forge_plugin_123.py"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        return
    monkeypatch.setattr(plugin_builder, "PLUGIN_DIR", str(plugin_dir))
    monkeypatch.setattr(code_forge, "generate_code", lambda _goal: _VALID_PLUGIN)
    monkeypatch.setattr(code_forge.time, "time_ns", lambda: 123)

    result = code_forge.forge_plugin("create a harmless plugin")

    assert result["success"] is False
    assert result["stage"] == "save_plugin"
    assert outside.read_text(encoding="utf-8") == "keep me"
