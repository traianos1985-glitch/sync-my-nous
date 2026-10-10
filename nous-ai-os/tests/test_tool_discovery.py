from executor.intent import detect_intent
from executor.tools import run_tool
from executor.tool_catalog import get_tool, tool_catalog


def test_intent_recognizes_new_utility_commands():
    assert detect_intent("calculate 2 + 2")["action"] == "calculate"
    assert detect_intent("convert 10 km to miles")["action"] == "convert"
    assert detect_intent("time Europe/Athens")["action"] == "current_time"
    assert detect_intent("text stats hello world")["action"] == "text_stats"
    assert detect_intent('json validate {"ok": true}')["action"] == "json_validate"
    assert detect_intent("sha256 NOUS")["action"] == "sha256"
    assert detect_intent("/tools")["action"] == "tool_catalog"


def test_run_tool_dispatches_utility_commands():
    assert run_tool({"action": "calculate"}, {"command": "calculate 5 * 9"})["result"] == 45
    assert run_tool({"action": "convert"}, {"command": "convert 100 cm to m"})["result"] == 1
    assert run_tool({"action": "current_time"}, {"command": "time"})["ok"] is True
    assert run_tool({"action": "text_stats"}, {"command": "text stats one two"})["words"] == 2
    assert run_tool({"action": "json_validate"}, {"command": 'json validate {"x": 1}'})["valid"] is True
    assert run_tool({"action": "sha256"}, {"command": "sha256 abc"})["characters"] == 3


def test_tool_catalog_is_discoverable_and_reports_risk():
    result = run_tool({"action": "tool_catalog"}, {})
    assert result["ok"] is True
    assert result["count"] >= 10
    names = {item["name"] for item in result["tools"]}
    assert {"calculate", "convert", "time", "text_stats", "json_validate", "sha256"} <= names
    assert get_tool("agent_solve")["approval_required"] == "depends_on_action"
    assert tool_catalog("utility")["count"] == 3
