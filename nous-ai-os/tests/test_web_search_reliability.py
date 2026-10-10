from __future__ import annotations

from executor import web_search


def test_search_rejects_empty_query():
    result = web_search.search("   ")
    assert result["ok"] is False
    assert result["error"] == "empty_query"
    assert result["results"] == []


def test_search_rejects_invalid_result_count():
    for value in (0, 11, True, "5", 1.5):
        result = web_search.search("weather", max_results=value)
        assert result["ok"] is False
        assert result["error"] == "invalid_max_results"


def test_search_propagates_engine_failure(monkeypatch):
    monkeypatch.setattr(
        "executor.internet_search_engine.search_web",
        lambda query, limit: {"ok": False, "error": "provider_unavailable", "results": []},
    )

    result = web_search.search("current events")

    assert result["ok"] is False
    assert result["error"] == "provider_unavailable"
    assert result["count"] == 0


def test_search_normalises_and_bounds_results(monkeypatch):
    monkeypatch.setattr(
        "executor.internet_search_engine.search_web",
        lambda query, limit: {
            "ok": True,
            "results": [
                {"title": " First ", "url": "https://example.org", "snippet": " Summary "},
                "malformed",
                {"title": "Second", "url": "https://example.net", "snippet": ""},
            ],
        },
    )

    result = web_search.search("query", max_results=1)

    assert result["ok"] is True
    assert result["count"] == 1
    assert result["results"][0]["title"] == "First"
    assert result["results"][0]["snippet"] == "Summary"


def test_search_status_does_not_claim_available_when_probe_fails(monkeypatch):
    monkeypatch.setattr(
        web_search,
        "search",
        lambda query, max_results: {
            "ok": False, "error": "search_unavailable", "results": [], "count": 0
        },
    )

    result = web_search.web_search_status()

    assert result["available"] is False
    assert result["error"] == "search_unavailable"



def test_internet_engine_marks_empty_search_as_no_results(monkeypatch, tmp_path):
    from executor import internet_search_engine

    monkeypatch.setattr(internet_search_engine, "_ddg_instant", lambda query: [])
    monkeypatch.setattr(internet_search_engine, "_wikipedia_search", lambda query: [])
    monkeypatch.setattr(internet_search_engine, "_ddg_html", lambda query, limit: [])
    monkeypatch.setattr(internet_search_engine, "CACHE", tmp_path / "cache.json")

    result = internet_search_engine.search_web("query", limit=3)

    assert result["ok"] is False
    assert result["error"] == "no_results"
    assert result["results"] == []
