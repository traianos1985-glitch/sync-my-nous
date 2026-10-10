import re

from flask import Flask

from executor.dashboard_api import dashboard_api_bp
from executor.intent import detect_intent
from executor.nous_ui import nous_dashboard_html
from executor.tool_catalog import get_tool, tool_catalog
from executor.tools import run_tool


def test_every_static_navigation_item_has_a_real_section():
    html = nous_dashboard_html()
    nav_ids = {
        value for value in re.findall(r'data-sec=["\']([^"\']+)["\']', html)
        if not value.startswith("${")
    }
    section_ids = set(re.findall(r'<section[^>]*id=["\']([^"\']+)["\']', html))
    assert nav_ids <= section_ids
    assert "toolbox" in nav_ids and "toolbox" in section_ids
    assert "tools" not in nav_ids and "tools" not in section_ids


def test_inline_button_handlers_resolve_to_declared_functions():
    html = nous_dashboard_html()
    functions = set(re.findall(r'(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(', html))
    handlers = set(re.findall(r'onclick=["\']\s*([A-Za-z_$][\w$]*)\s*\(', html))
    assert handlers <= functions


def test_tool_library_has_real_catalog_and_execution_endpoint_wiring():
    html = nous_dashboard_html()
    assert 'getJson("/api/tools/catalog")' in html
    assert 'postJson("/api/tools/run", {command: command})' in html
    assert 'id="toolboxCategory"' in html
    catalog = tool_catalog()
    names = [item["name"] for item in catalog["tools"]]
    assert len(names) == len(set(names))
    for name in ("calculate", "convert", "time", "text_stats", "json_validate", "sha256", "web_search", "agent_solve"):
        assert get_tool(name) is not None
    assert all(get_tool(name)["executable_from_tool_library"] is True for name in (
        "calculate", "convert", "time", "text_stats", "json_validate", "sha256"
    ))


def test_safe_utility_commands_are_routed_and_direct_run_is_allowlisted():
    examples = {
        "calculate 2 + 3": "calculate",
        "convert 12 km to miles": "convert",
        "time Europe/Athens": "current_time",
        "text stats hello world": "text_stats",
        'json validate {"ok":true}': "json_validate",
        "sha256 NOUS": "sha256",
    }
    for command, action in examples.items():
        intent = detect_intent(command)
        assert intent == {"type": "tool", "action": action}
        result = run_tool(intent, {"command": command})
        assert isinstance(result, dict) and result.get("ok") is True


def test_tool_library_api_runs_only_allowlisted_local_utilities():
    app = Flask(__name__)
    app.register_blueprint(dashboard_api_bp)
    client = app.test_client()

    catalog_response = client.get("/api/tools/catalog")
    assert catalog_response.status_code == 200
    assert catalog_response.get_json()["ok"] is True

    result = client.post("/api/tools/run", json={"command": "calculate 2 + 3"})
    assert result.status_code == 200
    assert result.get_json()["result"]["result"] == 5

    blocked = client.post("/api/tools/run", json={"command": "cmd whoami"})
    assert blocked.status_code == 403
    assert blocked.get_json()["error"] == "tool_not_allowlisted_for_direct_execution"
