from executor import multi_agent_team as team


def _base(monkeypatch, action, allowed):
    monkeypatch.setattr(team, "choose_master_priority", lambda: {"action": action})
    monkeypatch.setattr(team, "decide_next_action", lambda: {"next": "test"})
    monkeypatch.setattr(team, "check_action", lambda action, payload=None: {"allowed": allowed, "action": action})
    monkeypatch.setattr(team, "code_advice", lambda: {"ok": True})
    monkeypatch.setattr(team, "write_journal", lambda event, data: {"event": event})


def test_guardian_denial_prevents_specialist_execution(monkeypatch):
    _base(monkeypatch, "research_to_knowledge", False)
    calls = []
    monkeypatch.setattr(team, "researcher_agent", lambda **kwargs: calls.append("research"))
    monkeypatch.setattr(team, "builder_agent", lambda *args: calls.append("builder"))

    result = team.team_cycle(real_research=True)

    assert result["execution"]["status"] == "blocked"
    assert result["execution"]["reason"] == "guardian_denied_or_failed"
    assert result["researcher"] is None
    assert result["builder"] is None
    assert calls == []


def test_unknown_action_fails_closed(monkeypatch):
    _base(monkeypatch, "delete_files", False)
    calls = []
    monkeypatch.setattr(team, "researcher_agent", lambda **kwargs: calls.append("research"))
    monkeypatch.setattr(team, "builder_agent", lambda *args: calls.append("builder"))

    result = team.team_cycle()

    assert result["effective_action"] == "delete_files"
    assert result["execution"]["status"] == "blocked"
    assert calls == []


def test_allowed_research_reports_actual_role_failure(monkeypatch):
    _base(monkeypatch, "research_to_knowledge", True)
    monkeypatch.setattr(team, "research_status", lambda: {"ready": True})
    monkeypatch.setattr(team, "research_to_knowledge", lambda topic: (_ for _ in ()).throw(RuntimeError("source unavailable")))

    result = team.team_cycle(real_research=True)

    assert result["execution"]["status"] == "failed"
    assert result["execution"]["reason"] == "research_role_failed"
    assert result["researcher"]["status"] == "failed"
    assert "source unavailable" in result["researcher"]["error"]


def test_guardian_exception_blocks_specialist(monkeypatch):
    _base(monkeypatch, "act", True)
    monkeypatch.setattr(team, "check_action", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("policy unavailable")))
    calls = []
    monkeypatch.setattr(team, "builder_agent", lambda *args: calls.append("builder"))

    result = team.team_cycle()

    assert result["execution"]["status"] == "blocked"
    assert result["guardian"]["status"] == "failed"
    assert calls == []


def test_journal_failure_is_visible_without_faking_execution_failure(monkeypatch):
    _base(monkeypatch, "act", True)
    monkeypatch.setattr(team, "app_factory_status", lambda: {"ready": True})
    monkeypatch.setattr(team, "code_health", lambda: {"healthy": True})
    monkeypatch.setattr(team, "write_journal", lambda *args: (_ for _ in ()).throw(OSError("disk full")))

    result = team.team_cycle()

    assert result["execution"]["status"] == "completed"
    assert "disk full" in result["journal_error"]
