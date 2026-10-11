import executor.kernel as kernel


def test_catalogued_risky_tool_is_not_dispatched_before_approval(monkeypatch):
    monkeypatch.setattr(kernel, "save", lambda _entry: None)
    monkeypatch.setattr(kernel, "get_tool", lambda _name: {"approval_required": True})
    monkeypatch.setattr(kernel, "list_approvals", lambda status=None: [])
    monkeypatch.setattr(
        kernel,
        "request_approval",
        lambda action, payload, reason: {"id": 123, "action": action, "payload": payload},
    )
    dispatched = []
    monkeypatch.setattr(kernel, "run_tool", lambda *args: dispatched.append(args))

    result = kernel.handle("run plugin demo", {})

    assert result["type"] == "tool"
    assert result["output"]["approval_required"] is True
    assert result["output"]["approval_id"] == "123"
    assert result["output"]["action"] == "run_plugin"
    assert dispatched == []


def test_risky_tool_requires_matching_single_use_approval(monkeypatch):
    monkeypatch.setattr(kernel, "save", lambda _entry: None)
    monkeypatch.setattr(kernel, "get_tool", lambda _name: {"approval_required": True})
    monkeypatch.setattr(
        kernel,
        "claim_approved_approval",
        lambda approval_id, action, payload: None,
    )
    dispatched = []
    monkeypatch.setattr(kernel, "run_tool", lambda *args: dispatched.append(args))

    result = kernel.handle("run plugin demo", {"approval_id": "wrong-id"})

    assert result["output"]["error"] == "valid_approval_required"
    assert dispatched == []


def test_approved_risky_tool_runs_once_and_finishes_approval(monkeypatch):
    monkeypatch.setattr(kernel, "save", lambda _entry: None)
    monkeypatch.setattr(kernel, "get_tool", lambda _name: {"approval_required": True})
    monkeypatch.setattr(
        kernel,
        "claim_approved_approval",
        lambda approval_id, action, payload: {
            "id": approval_id,
            "action": action,
            "payload": payload,
        },
    )
    dispatched = []
    monkeypatch.setattr(
        kernel,
        "run_tool",
        lambda intent, context: dispatched.append((intent, context)) or {"ok": True},
    )
    finished = []
    monkeypatch.setattr(
        kernel,
        "finish_approval",
        lambda approval_id, status, result: finished.append((approval_id, status, result)),
    )

    result = kernel.handle("run plugin demo", {"approval_id": "123"})

    assert result["output"] == {"ok": True}
    assert result["approval_status"] == "completed"
    assert len(dispatched) == 1
    assert dispatched[0][0]["action"] == "run_plugin"
    assert finished[0][0:2] == ("123", "completed")


def test_shell_command_uses_its_dedicated_approval_workflow(monkeypatch):
    monkeypatch.setattr(kernel, "save", lambda _entry: None)
    monkeypatch.setattr(kernel, "get_tool", lambda _name: {"approval_required": True})
    dispatched = []
    monkeypatch.setattr(
        kernel,
        "run_tool",
        lambda intent, context: dispatched.append((intent, context))
        or {"ok": False, "approval_required": True, "approval_id": "shell-approval"},
    )

    result = kernel.handle("cmd pwd", {})

    assert result["output"]["approval_id"] == "shell-approval"
    assert result["output"]["approval_required"] is True
    assert dispatched[0][0]["action"] == "cmd"


def test_dynamic_agent_solve_requires_approval_when_it_will_generate_code(monkeypatch):
    monkeypatch.setattr(kernel, "save", lambda _entry: None)
    monkeypatch.setattr(
        kernel,
        "get_tool",
        lambda _name: {"approval_required": "depends_on_action"},
    )
    monkeypatch.setattr(kernel, "list_approvals", lambda status=None: [])
    monkeypatch.setattr(
        kernel,
        "request_approval",
        lambda action, payload, reason: {"id": 456, "action": action, "payload": payload},
    )
    dispatched = []
    monkeypatch.setattr(kernel, "run_tool", lambda *args: dispatched.append(args))

    result = kernel.handle("agent solve create a plugin", {})

    assert result["output"]["approval_required"] is True
    assert result["output"]["action"] == "agent_solve"
    assert result["output"]["approval_id"] == "456"
    assert dispatched == []


def test_dynamic_agent_solve_without_code_generation_keeps_normal_dispatch(monkeypatch):
    monkeypatch.setattr(kernel, "save", lambda _entry: None)
    monkeypatch.setattr(
        kernel,
        "get_tool",
        lambda _name: {"approval_required": "depends_on_action"},
    )
    monkeypatch.setattr(
        kernel,
        "run_tool",
        lambda intent, context: {"status": "completed", "action": intent["action"]},
    )

    result = kernel.handle("agent solve research the weather", {})

    assert result["output"]["status"] == "completed"
    assert result["output"]["action"] == "agent_solve"
