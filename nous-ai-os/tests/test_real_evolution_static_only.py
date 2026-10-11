"""Ensure autonomous evolution validates generated source without importing it."""
from executor import plugin_builder, real_evolution


def test_real_evolution_saves_generated_plugin_without_executing_source(tmp_path, monkeypatch) -> None:
    marker = tmp_path / "generated-source-executed.txt"
    source = (
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('executed')\n"
        "def run():\n"
        "    return {'ok': True}\n"
    )
    monkeypatch.setattr(real_evolution, "ask", lambda _prompt: {"response": source})
    monkeypatch.setattr(plugin_builder, "PLUGIN_DIR", str(tmp_path))

    result = real_evolution.RealEvolutionEngine().evolve("create a safe test plugin")

    assert result["status"] == "plugin_created"
    assert result["path"]
    assert not marker.exists()
