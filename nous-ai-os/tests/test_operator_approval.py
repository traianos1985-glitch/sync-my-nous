from executor import command_tools, operator_approval


def test_command_execution_requires_matching_single_use_approval(tmp_path, monkeypatch):
    monkeypatch.setattr(operator_approval, "FILE", str(tmp_path / "operator_approvals.json"))
    monkeypatch.setattr(command_tools.subprocess, "check_output", lambda *_a, **_k: "approved output")

    pending = command_tools.run_command("pwd")
    assert pending["ok"] is False
    assert pending["approval_required"] is True

    approval_id = pending["approval_id"]
    assert operator_approval.approve(approval_id) is not None
    result = command_tools.run_command("pwd", approval_id)
    repeated = command_tools.run_command("pwd", approval_id)

    assert result == {"ok": True, "output": "approved output"}
    assert repeated == {"ok": False, "error": "valid_approval_required"}
    assert operator_approval.get_approval(approval_id)["status"] == "completed"


def test_approval_cannot_be_reused_for_a_different_command(tmp_path, monkeypatch):
    monkeypatch.setattr(operator_approval, "FILE", str(tmp_path / "operator_approvals.json"))
    pending = command_tools.run_command("pwd")
    approval_id = pending["approval_id"]
    assert operator_approval.approve(approval_id) is not None

    result = command_tools.run_command("date", approval_id)

    assert result == {"ok": False, "error": "valid_approval_required"}
    assert operator_approval.get_approval(approval_id)["status"] == "approved"
