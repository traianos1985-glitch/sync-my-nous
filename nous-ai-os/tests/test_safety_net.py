import pytest


@pytest.fixture()
def safety(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import executor.safety_net as safety_net

    return safety_net


def test_status_empty(safety):
    status = safety.safety_status()
    assert status["ok"] is True
    assert status["summary"]["total"] == 0
    assert status["circuit"]["state"] == "closed"
    assert safety.list_incidents() == []


def test_circuit_opens_after_failures_and_resets(safety):
    for _ in range(safety.FAILURE_THRESHOLD):
        safety.record_incident("patch", "failure", error="boom")
    assert safety.safety_status()["circuit"]["state"] == "open"
    assert safety.allows_action() is False
    assert safety.reset_circuit()["circuit"]["state"] == "closed"
    assert safety.allows_action() is True


def test_manual_rollback_restores_backup(safety, tmp_path):
    from executor.rollback_engine import backup_file

    target = tmp_path / "file.txt"
    target.write_text("original")
    backup = backup_file(str(target))["backup"]
    target.write_text("broken")
    incident = safety.record_incident(
        "patch", "failure", files=[str(target)], backup_ids=[backup["id"]]
    )

    result = safety.manual_rollback(incident["id"])

    assert result["ok"] is True
    assert target.read_text() == "original"
    assert safety.manual_rollback(incident["id"])["error"] == "already_rolled_back"
    assert safety.safety_status()["summary"]["rollbacks"] >= 1


def test_manual_rollback_unknown_incident(safety):
    assert safety.manual_rollback("missing")["ok"] is False


def test_master_priority_handles_unknown_battery(monkeypatch):
    import executor.master_agent as master_agent

    monkeypatch.setattr(
        master_agent,
        "master_state",
        lambda: {
            "battery": {"alert": False, "level": None, "plugged": None},
            "queue": [],
            "learning": {"knowledge": {}},
        },
    )
    assert master_agent.choose_master_priority()["reason"] != "low_battery"
