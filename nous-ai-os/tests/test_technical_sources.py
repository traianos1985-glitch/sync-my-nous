import json

from executor import technical_sources as sources


def test_source_allowlist_is_small_and_uses_official_repositories():
    assert 0 < len(sources.OFFICIAL_SOURCES) <= sources.MAX_SOURCES
    assert all(source["url"].startswith("https://github.com/") for source in sources.OFFICIAL_SOURCES)
    assert all("/" in source["repository"] for source in sources.OFFICIAL_SOURCES)


def test_fetch_source_uses_fixed_host_and_disables_redirects(monkeypatch):
    captured = {}

    class Response:
        status_code = 302
        headers = {}
        def close(self):
            captured["closed"] = True

    def fake_get(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return Response()

    monkeypatch.setattr(sources.requests, "get", fake_get)
    result = sources._fetch_source(sources.OFFICIAL_SOURCES[0])

    assert result["ok"] is False
    assert result["error"] == "source_http_302"
    assert captured["url"].startswith("https://api.github.com/repos/python/cpython/releases")
    assert captured["allow_redirects"] is False
    assert captured["closed"] is True


def test_release_note_excerpt_is_bounded_and_plain_text():
    excerpt = sources._safe_excerpt("<p>Hello</p>\n" + "x" * 1000)
    assert "<p>" not in excerpt
    assert len(excerpt) <= 700


def test_scan_persists_report_and_marks_notes_untrusted(monkeypatch, tmp_path):
    monkeypatch.setattr(sources, "DATA_DIR", tmp_path)
    monkeypatch.setattr(sources, "REPORT_PATH", tmp_path / "report.json")
    monkeypatch.setattr(sources, "HISTORY_PATH", tmp_path / "history.json")
    monkeypatch.setattr(sources, "_fetch_source", lambda source: {
        "ok": True,
        "source": source["name"],
        "release_count": 1,
        "releases": [{
            "project": source["name"],
            "tag": "v1.2.3",
            "notes_are_untrusted_data": True,
            "action": "review_only",
        }],
    })

    report = sources.run_source_scan()

    assert report["ok"] is True
    assert report["status"] == "complete"
    assert report["release_count"] == len(sources.OFFICIAL_SOURCES)
    assert report["safety"]["release_text_executed"] is False
    assert json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))["status"] == "complete"
    assert len(json.loads((tmp_path / "history.json").read_text(encoding="utf-8"))) == 1


def test_missing_report_is_explicitly_not_scanned(monkeypatch, tmp_path):
    monkeypatch.setattr(sources, "REPORT_PATH", tmp_path / "missing.json")
    report = sources.latest_source_report()
    assert report["status"] == "not_scanned"
    assert report["sources"] == []


def test_scan_if_due_skips_recent_and_runs_stale(monkeypatch, tmp_path):
    monkeypatch.setattr(sources, "REPORT_PATH", tmp_path / "report.json")
    monkeypatch.setattr(sources, "HISTORY_PATH", tmp_path / "history.json")
    monkeypatch.delenv("NOUS_TECH_WATCH_INTERVAL", raising=False)
    calls = []
    monkeypatch.setattr(sources, "run_source_scan", lambda: calls.append(1) or {"ok": True, "status": "complete", "checked_at": 1000.0, "release_count": 2})
    # never scanned -> runs
    assert sources.scan_if_due(now=1000.0)["ran"] is True
    sources._atomic_json(sources.REPORT_PATH, {"checked_at": 1000.0})
    # 1 hour later with a 24h interval -> skipped
    skipped = sources.scan_if_due(now=1000.0 + 3600)
    assert skipped["ran"] is False and skipped["next_due_at"] == 1000.0 + 86400
    # after 24h -> runs again
    assert sources.scan_if_due(now=1000.0 + 86400)["ran"] is True
    assert len(calls) == 2


def test_watch_interval_has_one_hour_floor(monkeypatch):
    monkeypatch.setenv("NOUS_TECH_WATCH_INTERVAL", "60")
    assert sources.watch_interval() == 3600
    monkeypatch.setenv("NOUS_TECH_WATCH_INTERVAL", "bad")
    assert sources.watch_interval() == 86400


def test_status_reports_periodic_watch_needs_autonomy(monkeypatch, tmp_path):
    monkeypatch.setattr(sources, "REPORT_PATH", tmp_path / "missing.json")
    status = sources.source_watch_status()
    assert status["automatic_updates"] is False
    assert status["periodic_watch"]["requires_autonomy_enabled"] is True
