"""Regression tests για proposal-first autonomy και tamper-evident journal."""

import importlib


def test_journal_integrity_detects_tampering(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import executor.agent_journal as journal
    journal = importlib.reload(journal)

    journal.write_journal("plan_created", {"goal": "test"})
    assert journal.verify_journal()["ok"] is True

    items = journal._load()
    items[0]["event"] = "tampered"
    journal._save(items)
    assert journal.verify_journal()["ok"] is False


def test_workspace_path_is_confined(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import executor.autonomous_agent as agent
    agent = importlib.reload(agent)

    assert agent.inspect_file("missing.py")["error"] == "file_not_found"
    try:
        agent.inspect_file("../outside.py")
    except ValueError as exc:
        assert "εκτός workspace" in str(exc)
    else:
        raise AssertionError("workspace escape was not rejected")


def test_only_allowlisted_checks_can_run(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import executor.autonomous_agent as agent
    agent = importlib.reload(agent)

    result = agent.run_check("shell_command")
    assert result["ok"] is False
    assert "python_compile" in result["allowed"]
    assert "journal_integrity" in result["allowed"]


def test_proposals_require_approval(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import executor.autonomous_agent as agent
    agent = importlib.reload(agent)

    result = agent.propose_code("add feature", "feature.py", "VALUE = 1")
    assert result["ok"] is True
    assert result["requires_approval"] is True
    assert agent.pending_proposals()["proposals"][0]["status"] == "pending_approval"
    approved = agent.approve_proposal(result["proposal"]["id"])
    assert approved["status"] == "approved_not_applied"
