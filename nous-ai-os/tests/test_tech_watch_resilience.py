import json
import time

from executor import technical_sources as sources
from executor import upgrade_planner as planner


def test_source_scan_runs_sources_concurrently_and_preserves_configured_order(monkeypatch, tmp_path):
    monkeypatch.setattr(sources, "DATA_DIR", tmp_path)
    monkeypatch.setattr(sources, "REPORT_PATH", tmp_path / "report.json")
    monkeypatch.setattr(sources, "HISTORY_PATH", tmp_path / "history.json")

    def fake_fetch(source):
        time.sleep(0.03)
        return {
            "ok": True,
            "source": source["name"],
            "release_count": 0,
            "releases": [],
        }

    monkeypatch.setattr(sources, "_fetch_source", fake_fetch)
    started = time.monotonic()
    report = sources.run_source_scan()
    elapsed = time.monotonic() - started

    assert report["status"] == "complete"
    assert [item["source"] for item in report["sources"]] == [
        item["name"] for item in sources.OFFICIAL_SOURCES[:sources.MAX_SOURCES]
    ]
    # Five sources sleeping 30 ms should finish substantially faster than
    # five sequential sleeps; generous tolerance avoids flaky CI timing.
    assert elapsed < 0.14
    assert json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))["status"] == "complete"


def test_source_scan_converts_unexpected_worker_errors_to_partial_report(monkeypatch, tmp_path):
    monkeypatch.setattr(sources, "DATA_DIR", tmp_path)
    monkeypatch.setattr(sources, "REPORT_PATH", tmp_path / "report.json")
    monkeypatch.setattr(sources, "HISTORY_PATH", tmp_path / "history.json")

    def fake_fetch(source):
        if source["name"] == sources.OFFICIAL_SOURCES[0]["name"]:
            raise RuntimeError("private detail")
        return {"ok": True, "source": source["name"], "release_count": 0, "releases": []}

    monkeypatch.setattr(sources, "_fetch_source", fake_fetch)
    report = sources.run_source_scan()

    assert report["status"] == "partial"
    assert report["successful_source_count"] == len(sources.OFFICIAL_SOURCES) - 1
    assert report["sources"][0]["error"] == "RuntimeError"
    assert "private detail" not in json.dumps(report)


def test_release_proposal_reports_unavailable_evidence_as_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(planner, "FILE", str(tmp_path / "plans.json"))
    monkeypatch.setattr(
        "executor.release_triage.triage_latest_releases",
        lambda limit=25: {
            "ok": True,
            "status": "unavailable",
            "items_count": 0,
            "items": [],
        },
    )

    result = planner.propose_release_evidence_plans()

    assert result["ok"] is False
    assert result["error"] == "release_evidence_unavailable"
    assert result["source_queue_status"] == "unavailable"
    assert result["created_count"] == 0
    assert result["plans"] == []
    assert result["safety"]["code_executed"] is False


def test_release_proposal_still_allows_partial_but_real_evidence(monkeypatch, tmp_path):
    monkeypatch.setattr(planner, "FILE", str(tmp_path / "plans.json"))
    item = {
        "project": "Python",
        "repository": "python/cpython",
        "release": "Python release",
        "tag": "v99.1.0",
        "published_at": "2026-10-01T12:00:00Z",
        "source_url": "https://github.com/python/cpython/releases/tag/v99.1.0",
        "evidence_excerpt": "Security fix for a vulnerability.",
        "signals": ["security"],
        "priority": "high",
        "confidence": "keyword_signal",
        "status": "needs_human_review",
        "action": "review_only",
    }
    monkeypatch.setattr(
        "executor.release_triage.triage_latest_releases",
        lambda limit=25: {"status": "partial", "items": [item]},
    )

    result = planner.propose_release_evidence_plans()

    assert result["ok"] is True
    assert result["created_count"] == 1
    assert result["source_queue_status"] == "partial"
