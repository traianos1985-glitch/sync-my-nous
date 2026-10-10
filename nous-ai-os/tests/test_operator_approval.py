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


def test_approval_payload_must_match_and_execution_is_single_use(tmp_path, monkeypatch):
    monkeypatch.setattr(operator_approval, "FILE", str(tmp_path / "operator_approvals.json"))
    payload = {"target": "test", "dry_run": True}
    approval = operator_approval.request_approval("deploy", payload=payload)
    assert operator_approval.approve(approval["id"]) is not None

    assert operator_approval.claim_approved_approval(
        approval["id"], "deploy", {"target": "production", "dry_run": True}
    ) is None
    claimed = operator_approval.claim_approved_approval(
        approval["id"], "deploy", payload
    )
    assert claimed["status"] == "executing"
    assert operator_approval.claim_approved_approval(
        approval["id"], "deploy", payload
    ) is None

    finished = operator_approval.finish_approval(
        approval["id"], "completed", {"ok": True}
    )
    assert finished["status"] == "completed"
    assert operator_approval.finish_approval(
        approval["id"], "completed", {"ok": True}
    ) is None


def test_rejected_approval_cannot_be_claimed(tmp_path, monkeypatch):
    monkeypatch.setattr(operator_approval, "FILE", str(tmp_path / "operator_approvals.json"))
    approval = operator_approval.request_approval("deploy", payload={"target": "test"})
    assert operator_approval.reject(approval["id"]) is not None
    assert operator_approval.claim_approved_approval(
        approval["id"], "deploy", {"target": "test"}
    ) is None
