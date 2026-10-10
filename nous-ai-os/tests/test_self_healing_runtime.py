def test_unhealthy_self_heal_only_diagnoses_and_records(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import executor.self_healing_runtime as runtime

    saved = []
    monkeypatch.setattr(runtime, "repair_check", lambda: {"healthy": False, "issues": ["test"]})
    monkeypatch.setattr(runtime, "save", lambda event: saved.append(event))

    result = runtime.self_heal_check()

    assert result["checked"] is True
    assert result["healthy"] is False
    assert result["action"] == "diagnose_only"
    assert "χωρίς έγκριση" in result["note"]
    assert saved and saved[0]["event"] == "self_heal_check"


def test_healthy_self_heal_does_not_attempt_repair(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import executor.self_healing_runtime as runtime

    saved = []
    monkeypatch.setattr(runtime, "repair_check", lambda: {"healthy": True})
    monkeypatch.setattr(runtime, "save", lambda event: saved.append(event))

    result = runtime.self_heal_check()

    assert result["healthy"] is True
    assert result["action"] == "none"
    assert "note" not in result
    assert saved[0]["result"]["action"] == "none"


def test_self_heal_treats_malformed_health_result_as_unhealthy(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import executor.self_healing_runtime as runtime

    monkeypatch.setattr(runtime, "repair_check", lambda: None)
    monkeypatch.setattr(runtime, "save", lambda _event: None)

    result = runtime.self_heal_check()

    assert result["healthy"] is False
    assert result["action"] == "diagnose_only"
