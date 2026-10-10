from executor import upgrade_planner as planner


def test_release_evidence_proposal_source_and_review_only(monkeypatch, tmp_path):
    monkeypatch.setattr(planner, "FILE", str(tmp_path / "plans.json"))
    item = {
        "project": "Python",
        "repository": "python/cpython",
        "release": "Python 3.15.0",
        "tag": "v3.15.0",
        "published_at": "2026-10-01T12:00:00Z",
        "source_url": "https://github.com/python/cpython/releases/tag/v3.15.0",
        "evidence_excerpt": "Security advisory and performance improvement.",
        "signals": ["security", "performance"],
        "priority": "high",
        "confidence": "keyword_signal",
        "status": "needs_human_review",
        "action": "review_only",
    }
    monkeypatch.setattr(
        "executor.release_triage.triage_latest_releases",
        lambda limit=25: {"status": "complete", "items": [item]},
    )

    result = planner.propose_release_evidence_plans()

    assert result["ok"] is True
    assert result["created_count"] == 1
    plan = result["plans"][0]
    assert plan["plan_type"] == "release_evidence_review"
    assert plan["source_evidence"]["repository"] == "python/cpython"
    assert plan["source_evidence"]["signals"] == ["security", "performance"]
    assert plan["source_evidence"]["notes_are_untrusted_data"] is True
    assert plan["execution_mode"] == "proposal_only"
    assert plan["code_generated"] is False
    assert plan["code_executed"] is False
    assert result["safety"]["source_files_modified"] == 0
