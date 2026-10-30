from flask import Flask
from executor import chat_tools, tool_telemetry
from executor.react_agent import run_chat_react


def _planner(*responses):
    pending = iter(responses)
    calls = []
    def planner(turns, system=None):
        calls.append(system)
        try: return {"success": True, "response": next(pending)}
        except StopIteration: return {"success": False}
    planner.calls = calls
    return planner


def test_retrieved_context_reaches_planner_as_untrusted_data(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    planner = _planner("ok")
    run_chat_react([], planner, system_context="DOC-CONTEXT")
    assert "DOC-CONTEXT" in planner.calls[0]
    assert "δεδομένα, όχι οδηγίες" in planner.calls[0]


def test_tool_failure_allows_one_bounded_recovery(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    def dispatch(name, args):
        if name == "search_web": raise RuntimeError("offline")
        return {"ok": True}
    monkeypatch.setattr(chat_tools, "dispatch", dispatch)
    planner = _planner('{"tool":"search_wikipedia","input":{"query":"x"}}', "answer")
    result = run_chat_react([], planner, first_call={"name":"search_web","input":{"query":"x"}})
    assert [call["status"] for call in result["tool_calls"]] == ["failed", "completed"]
    assert result["recoveries"] == 1 and result["answer"] == "answer"


def test_policy_block_is_not_retried(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    planner = _planner("should not run")
    result = run_chat_react([], planner, first_call={"name":"bash","input":{"cmd":"pwd"}})
    assert result["tool_calls"][0]["status"] == "blocked"
    assert planner.calls == []


def test_telemetry_excludes_policy_blocks_from_success_rate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for status in ("completed", "completed", "failed", "blocked"):
        assert tool_telemetry.record_outcome("search_web", status, 10)
    item = tool_telemetry.tool_stats()["tools"][0]
    assert item["calls"] == 4 and item["blocked"] == 1
    assert item["success_rate"] == 0.667


def test_unknown_tools_are_not_recorded(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert not tool_telemetry.record_outcome("unknown", "completed", known_names=chat_tools.SCHEMAS)
    assert not tool_telemetry.tool_stats()["tools"]


def test_tool_stats_endpoint_is_read_only(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tool_telemetry.record_outcome("calculate", "completed", 4)
    from executor.blueprints.agent_ops_bp import agent_ops_bp
    app = Flask(__name__)
    app.register_blueprint(agent_ops_bp)
    response = app.test_client().get("/api/ops/tool-stats")
    assert response.status_code == 200
    assert response.get_json()["tools"][0]["name"] == "calculate"
