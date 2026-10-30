from executor import command_tools


def test_blocks_dangerous_arguments_even_for_allowlisted_commands(monkeypatch):
    def unexpected_approval(*_args, **_kwargs):
        raise AssertionError("unsafe commands must be rejected before approval")

    monkeypatch.setattr(command_tools, "request_approval", unexpected_approval)

    assert command_tools.run_command("ls -R /")["error"] == "command_arguments_blocked"
    assert command_tools.run_command("date -s 2020-01-01")["error"] == "command_arguments_blocked"
    assert command_tools.run_command("pwd /etc")["error"] == "command_arguments_blocked"
    assert command_tools.run_command("whoami --help")["error"] == "command_arguments_blocked"
    assert command_tools.run_command("ls --help")["error"] == "command_arguments_blocked"


def test_safe_read_only_command_forms_still_require_approval(monkeypatch):
    seen = []

    def approval(kind, payload, reason):
        seen.append((kind, payload, reason))
        return {"id": "approval-123"}

    monkeypatch.setattr(command_tools, "request_approval", approval)

    result = command_tools.run_command("ls -la")
    assert result["approval_required"] is True
    assert result["approval_id"] == "approval-123"
    assert seen[0][0] == "command_execution"
    assert seen[0][1] == {"command": "ls -la"}


def test_exact_git_status_command_remains_available_behind_approval(monkeypatch):
    seen = []
    monkeypatch.setattr(
        command_tools,
        "request_approval",
        lambda kind, payload, reason: seen.append(payload) or {"id": "git-approval"},
    )

    result = command_tools.run_command("git status --short")

    assert result["approval_required"] is True
    assert seen == [{"command": "git status --short"}]


def test_rejects_non_string_and_control_character_commands():
    assert command_tools.run_command(None)["error"] == "empty_command"
    assert command_tools.run_command("pwd\nwhoami")["error"] == "invalid_command"
    assert command_tools.run_command("x" * 513)["error"] == "invalid_command"
