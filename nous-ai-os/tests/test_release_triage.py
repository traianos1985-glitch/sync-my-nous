from executor import release_triage as triage


def _release(**overrides):
    value = {
        "project": "Python",
        "repository": "python/cpython",
        "tag": "v3.15.0",
        "name": "Python 3.15.0",
        "published_at": "2026-10-01T12:00:00Z",
        "url": "https://github.com/python/cpython/releases/tag/v3.15.0",
        "notes_excerpt": "Security fix and performance improvement.",
    }
    value.update(overrides)
    return value


def test_security_and_performance_signals_are_classified_without_execution():
    result = triage.triage_release(_release())

    assert result["signals"] == ["security", "performance"]
    assert result["priority"] == "high"
    assert result["status"] == "needs_human_review"
    assert result["action"] == "review_only"
    assert result["code_generated"] is False
    assert result["code_executed"] is False


def test_breaking_change_gets_high_priority():
    result = triage.triage_release(_release(notes_excerpt="This release has breaking changes."))

    assert "breaking_change" in result["signals"]
    assert result["priority"] == "high"


def test_unclassified_release_still_requires_human_review():
    result = triage.triage_release(_release(notes_excerpt="Several small updates."))

    assert result["signals"] == ["manual_review"]
    assert result["priority"] == "review"
    assert result["confidence"] == "unclassified"


def test_triage_ignores_unknown_repository_and_arbitrary_source_url():
    report = {
        "status": "complete",
        "sources": [{
            "ok": True,
            "releases": [
                _release(repository="attacker/repo", url="https://example.com/"),
                _release(url="https://example.com/payload"),
            ],
        }],
    }

    result = triage.triage_latest_releases(report)

    assert result["items"] == []
    assert result["safety"]["requires_human_review"] is True


def test_triage_deduplicates_repository_and_tag_and_bounds_results():
    release = _release()
    report = {
        "status": "complete",
        "sources": [
            {"ok": True, "releases": [release, dict(release)]},
            {"ok": True, "releases": [_release(tag="v3.14.9")]},
        ],
    }

    result = triage.triage_latest_releases(report, limit=1)

    assert result["items_count"] == 1
    assert result["items"][0]["tag"] == "v3.15.0"
    assert result["safety"]["upgrade_plans_created"] is False
