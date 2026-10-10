from executor.intent import detect_intent
from executor.tools import run_tool


def test_new_utility_commands_route_to_real_tools():
    cases = {
        "calculate 2 + 2": "calculate",
        "convert 12 km to miles": "convert",
        "time Europe/Athens": "current_time",
        "text stats hello world": "text_stats",
        'json validate {"ok":true}': "json_validate",
        "sha256 NOUS": "sha256",
        'json format {"ok":true}': "json_format",
        "url encode hello world": "url_encode",
        "url decode hello%20world": "url_decode",
        "tools": "tool_catalog",
        "εργαλεία": "tool_catalog",
    }
    for command, action in cases.items():
        intent = detect_intent(command)
        assert intent == {"type": "tool", "action": action}


def test_new_utility_commands_execute_via_existing_tool_dispatch():
    assert run_tool(detect_intent("calculate 2 + 2"), {"command": "calculate 2 + 2"})["result"] == 4
    assert run_tool(detect_intent("convert 1 km to m"), {"command": "convert 1 km to m"})["result"] == 1000
    assert run_tool(detect_intent("text stats hello world"), {"command": "text stats hello world"})["words"] == 2
    assert run_tool(detect_intent('json validate {"ok":true}'), {"command": 'json validate {"ok":true}'})["valid"] is True
    assert len(run_tool(detect_intent("sha256 NOUS"), {"command": "sha256 NOUS"})["sha256"]) == 64
    assert run_tool(detect_intent('json format {"ok":true}'), {"command": 'json format {"ok":true}'})["formatted"] == '{\n  "ok": true\n}'
    assert run_tool(detect_intent("url encode hello world"), {"command": "url encode hello world"})["encoded"] == "hello%20world"
    assert run_tool(detect_intent("url decode hello%20world"), {"command": "url decode hello%20world"})["decoded"] == "hello world"


def test_tool_catalog_includes_new_and_legacy_tool_entries():
    catalog = run_tool(detect_intent("tools"), {"command": "tools"})
    names = {item["name"] for item in catalog["tools"]}
    assert {"calculate", "convert", "time", "text_stats", "json_validate", "sha256"} <= names
    assert {"memory", "web_search", "agent_solve", "autonomy_start", "repair_system"} <= names
    assert catalog["count"] == len(catalog["tools"])
