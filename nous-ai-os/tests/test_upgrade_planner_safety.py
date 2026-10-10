import json

from executor import upgrade_planner as planner


def test_approve_only_marks_plan_for_review_without_execution(monkeypatch, tmp_path):
    path = tmp_path / "upgrade_plans.json"
    monkeypatch.setattr(planner, "FILE", str(path))
    plan = {
        "id": "123",
        "status": "pending",
        "upgrades": [{"title": "example", "file": "unsafe.py"}],
        "execution_log": [],
    }
    planner._save([plan])

    result = planner.approve_upgrade_plan("123")

    assert result["ok"] is True
    assert result["approved_for_review"] is True
    assert result["code_generated"] is False
    assert result["code_executed"] is False
    stored = json.loads(path.read_text(encoding="utf-8"))[0]
    assert stored["status"] == "approved"
    assert stored["execution_mode"] == "proposal_only"
    assert any("Δεν δημιουργήθηκε ούτε εκτελέστηκε κώδικας" in line for line in stored["execution_log"])
    assert not (tmp_path / "unsafe.py").exists()


def test_approval_rejects_non_pending_plan(monkeypatch, tmp_path):
    monkeypatch.setattr(planner, "FILE", str(tmp_path / "plans.json"))
    planner._save([{"id": "a", "status": "approved"}])

    result = planner.approve_upgrade_plan("a")

    assert result["ok"] is False
    assert result["error"] == "plan_not_pending"


def test_proposal_is_explicitly_proposal_only(monkeypatch, tmp_path):
    monkeypatch.setattr(planner, "FILE", str(tmp_path / "plans.json"))

    result = planner.propose_upgrade_plan()

    assert result["ok"] is True
    assert result["plan"]["status"] == "pending"
    assert result["plan"]["execution_mode"] == "proposal_only"
    assert planner.upgrade_planner_status()["execution_enabled"] is False


def test_recent_approved_plan_deduplicates(monkeypatch, tmp_path):
    monkeypatch.setattr(planner, "FILE", str(tmp_path / "plans.json"))
    planner._save([{"id": "recent", "status": "approved", "approved": 9999999999}])

    result = planner.propose_upgrade_plan()

    assert result["ok"] is True
    assert result["deduped"] is True
    assert result["plan"]["id"] == "recent"
