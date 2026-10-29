import json

from executor import chat_tools
from executor.react_agent import run_chat_react


def planner(*responses):
    values = iter(responses)
    return lambda *_a, **_k: {"success": True, "response": next(values)}


def test_real_workspace_read_and_events(monkeypatch, tmp_path):
    from executor import react_agent
    monkeypatch.setattr(react_agent, "WORKSPACE", tmp_path)
    (tmp_path / "note.txt").write_text("actual file content")
    events = []
    result = run_chat_react([], planner("Read completed"), first_call={"name": "read_file", "input": {"path": "note.txt"}}, on_event=lambda k, v: events.append(v))
    assert [e["status"] for e in events] == ["running", "completed"]
    assert events[0]["id"] == events[1]["id"]
    assert result["tool_calls"][0]["output"] == "actual file content"
    assert result["executed"] is True


def test_multiple_model_selected_tools_and_bound(monkeypatch):
    seen = []
    monkeypatch.setattr(chat_tools, "dispatch", lambda name, args: seen.append(name) or {"ok": True})
    steps = [json.dumps({"tool": n, "input": {}}) for n in ["system_status", "missions_status"]]
    result = run_chat_react([], planner(*steps, "Done"))
    assert seen == ["system_status", "missions_status"]
    assert len(result["tool_calls"]) == 2
    seen.clear()
    run_chat_react([], planner(*steps), max_steps=1)
    assert seen == ["system_status"]


def test_duplicate_never_replayed(monkeypatch):
    seen = []
    monkeypatch.setattr(chat_tools, "dispatch", lambda *a: seen.append(a) or {})
    call = '{"tool":"system_status","input":{}}'
    run_chat_react([], planner(call, call))
    assert len(seen) == 1


def test_blocked_unknown_and_invalid_arguments(monkeypatch):
    monkeypatch.setattr(chat_tools, "dispatch", lambda *a: (_ for _ in ()).throw(AssertionError("must not dispatch")))
    assert chat_tools.execute_call("bash", {"cmd": "pwd"})["status"] == "blocked"
    assert chat_tools.execute_call("system_status", {"unexpected": True})["status"] == "blocked"
    assert chat_tools.execute_call("search_web", {"query": "news"}, allow_web=False)["status"] == "blocked"


def test_traversal_private_and_missing_files_not_completed(monkeypatch, tmp_path):
    from executor import react_agent
    monkeypatch.setattr(react_agent, "WORKSPACE", tmp_path)
    for path in ["../outside.txt", ".env", "secret.key", "missing.txt"]:
        result = chat_tools.execute_call("read_file", {"path": path})
        assert result["status"] in {"blocked", "failed"}
        assert result["executed"] is False


def test_synthesis_failure_preserves_result(monkeypatch):
    seen = []
    monkeypatch.setattr(chat_tools, "dispatch", lambda *a: seen.append(a) or {"count": 7})
    result = run_chat_react([], lambda *a, **k: {"success": False}, first_call={"name": "missions_status", "input": {}})
    assert result["tool_calls"][0]["output"] == {"count": 7}
    assert len(seen) == 1


def test_cancel_does_not_start_next_tool(monkeypatch):
    seen = []
    monkeypatch.setattr(chat_tools, "dispatch", lambda *a: seen.append(a) or {})
    run_chat_react([], planner("Done"), first_call={"name": "system_status", "input": {}}, cancelled=lambda: True)
    assert seen == []


def test_chat_http_stream_uses_real_tool(monkeypatch, tmp_path):
    from executor import router, react_agent, remote_llm, conversation_manager
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(router, "check_token", lambda _r: True)
    # Isolated test app retains the route's explicit auth check, without production bootstrap hooks.
    from flask import Flask
    app = Flask(__name__)
    app.add_url_rule("/chat", view_func=router.chat, methods=["POST"])
    monkeypatch.setattr(react_agent, "WORKSPACE", tmp_path)
    (tmp_path / "report.txt").write_text("verified result")
    monkeypatch.setattr(remote_llm, "ask_with_turns", planner("Finished"))
    monkeypatch.setattr(conversation_manager, "append_turn", lambda **k: {"conversation_id": "123"})
    response = app.test_client().post("/chat", json={"message": "read file report.txt", "tool_execution": True, "stream": True})
    assert response.status_code == 200
    payload = response.get_data(as_text=True)
    assert payload.count("event: tool") == 2
    assert "verified result" in payload
    assert "event: result" in payload


def test_route_rejects_unauthorized_before_tools(monkeypatch):
    from executor import router
    from flask import Flask
    app = Flask(__name__)
    app.add_url_rule("/chat", view_func=router.chat, methods=["POST"])
    monkeypatch.setattr(router, "check_token", lambda _r: False)
    monkeypatch.setattr(chat_tools, "dispatch", lambda *a: (_ for _ in ()).throw(AssertionError("must not run")))
    assert app.test_client().post("/chat", json={"message": "system status"}).status_code == 401