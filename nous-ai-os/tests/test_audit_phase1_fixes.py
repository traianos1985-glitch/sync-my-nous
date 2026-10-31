import os
import sys
import tempfile
from pathlib import Path
import pytest

from executor.agent_loop import _run_tool
from executor.knowledge_memory_engine import KNOWLEDGE_FILE, save_json, load_json


def test_search_memory_dict_handling_n04(monkeypatch, tmp_path):
    """N-04: Ensure search_memory correctly processes dict hits and extracts answer/snippet."""
    test_file = tmp_path / "knowledge.json"
    monkeypatch.setattr("executor.knowledge_memory_engine.KNOWLEDGE_FILE", test_file)
    
    # Test empty memory
    save_json(test_file, [])
    res = _run_tool("search_memory", "οτιδήποτε")
    assert res == "Δεν βρήκα σχετική μνήμη."

    # Test memory with answer field
    save_json(test_file, [{
        "question": "Ποιο είναι το μυστικό;",
        "answer": "Η απάντηση είναι 42 και λειτουργεί αξιόπιστα.",
        "tags": ["μυστικό"],
        "updated_at": "2026-10-31"
    }])
    res = _run_tool("search_memory", "μυστικό")
    assert "42" in res
    assert "αξιόπιστα" in res


def test_app_runner_secrets_isolation_n01(monkeypatch):
    """N-01: Ensure _launch_app_proc strips sensitive credentials and sets cwd to app root."""
    with tempfile.TemporaryDirectory() as tmpdir:
        app_dir = Path(tmpdir).resolve()
        script_path = app_dir / "main.py"
        script_path.write_text("""
import os
import sys

forbidden = ["GEMINI_API_KEY", "NOUS_TOKEN", "RENDER_API_KEY", "MY_SUPER_SECRET"]
found = [k for k in forbidden if k in os.environ]
print(f"CWD:{os.getcwd()}")
print(f"FOUND:{found}")
""")
        monkeypatch.setenv("GEMINI_API_KEY", "test_gemini_key_12345")
        monkeypatch.setenv("NOUS_TOKEN", "test_nous_token_67890")
        monkeypatch.setenv("RENDER_API_KEY", "test_render_key_abcde")
        monkeypatch.setenv("MY_SUPER_SECRET", "super_secret_xyz")

        from executor.router import _launch_app_proc, _running_apps
        cmd = f"{sys.executable} {script_path}"
        res = _launch_app_proc(cmd, "isolated_test_app", app_dir)
        proc = res["proc"]
        proc.wait(timeout=5)
        output = "".join(res["lines"])

        assert f"CWD:{app_dir}" in output
        assert "FOUND:[]" in output
