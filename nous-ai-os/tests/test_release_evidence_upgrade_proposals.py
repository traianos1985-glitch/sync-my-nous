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



def test_release_proposals_deduplicate_repository_and_tag(monkeypatch, tmp_path):
    monkeypatch.setattr(planner, "FILE", str(tmp_path / "plans.json"))
    item = {
        "project": "Python",
        "repository": "python/cpython",
        "release": "Python 3.15.0",
        "tag": "v3.15.0",
        "published_at": "2026-10-01T12:00:00Z",
        "source_url": "https://github.com/python/cpython/releases/tag/v3.15.0",
        "evidence_excerpt": "Security advisory.",
        "signals": ["security"],
        "priority": "high",
        "confidence": "keyword_signal",
        "status": "needs_human_review",
        "action": "review_only",
    }
    monkeypatch.setattr(
        "executor.release_triage.triage_latest_releases",
        lambda limit=25: {"status": "complete", "items": [item, dict(item)]},
    )

    first = planner.propose_release_evidence_plans()
    second = planner.propose_release_evidence_plans()

    assert first["created_count"] == 1
    assert first["deduped_count"] == 1
    assert second["created_count"] == 0
    assert second["deduped_count"] == 1


def test_release_proposals_reject_untrusted_urls_and_manual_only_items(monkeypatch, tmp_path):
    monkeypatch.setattr(planner, "FILE", str(tmp_path / "plans.json"))
    item = {
        "project": "Python",
        "repository": "python/cpython",
        "release": "Python 3.15.0",
        "tag": "v3.15.0",
        "source_url": "https://example.invalid/payload",
        "signals": ["security"],
        "status": "needs_human_review",
        "action": "review_only",
    }
    manual = dict(item, source_url="https://github.com/python/cpython/releases/tag/v3.15.0", signals=["manual_review"])
    monkeypatch.setattr(
        "executor.release_triage.triage_latest_releases",
        lambda limit=25: {"status": "complete", "items": [item, manual]},
    )

    result = planner.propose_release_evidence_plans()

    assert result["ok"] is True
    assert result["created_count"] == 0
    assert not (tmp_path / "plans.json").exists()


def test_release_proposal_limit_is_bounded(monkeypatch, tmp_path):
    monkeypatch.setattr(planner, "FILE", str(tmp_path / "plans.json"))
    for limit in (0, -1, True, 11, "invalid"):
        result = planner.propose_release_evidence_plans(limit)
        assert result["ok"] is False
        assert result["error"] == "invalid_limit"
