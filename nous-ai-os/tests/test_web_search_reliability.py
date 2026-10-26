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


def test_search_status_reports_unknown_when_empty_results_are_ambiguous(monkeypatch):
    monkeypatch.setattr(
        web_search,
        "search",
        lambda query, max_results: {
            "ok": False, "error": "no_results", "results": [], "count": 0
        },
    )

    result = web_search.web_search_status()

    assert result["available"] is None
    assert result["status"] == "unknown"


def test_filter_relevant_detects_low_score_for_product_query():
    from executor.internet_search_engine import _filter_relevant

    weak = [
        {"title": "Shiny - Wikipedia", "url": "https://en.wikipedia.org/wiki/Shiny", "snippet": "Shiny is an R package"},
        {"title": "GeForce Now", "url": "https://www.nvidia.com/geforce-now", "snippet": "cloud gaming"},
    ]
    ranked, top, low = _filter_relevant("Render free tier", weak)
    assert low is True
    assert top < 1.5

    strong = [
        {
            "title": "Render Free Tier",
            "url": "https://render.com/docs/free",
            "snippet": "Render free tier includes static sites and web services",
        },
    ]
    ranked2, top2, low2 = _filter_relevant("Render free tier", strong)
    assert low2 is False
    assert top2 >= 1.5
    assert ranked2[0].get("relevance_score", 0) >= 1.5


def test_detect_product_sites_for_render_and_vercel():
    from executor.internet_search_engine import _detect_product_sites, _product_site_queries

    hosts = _detect_product_sites("Render free tier")
    assert "render.com" in hosts
    assert "docs.render.com" in hosts

    queries = _product_site_queries("Render free tier")
    assert queries
    assert "site:render.com" in queries[0]

    assert _detect_product_sites("random weather athens") == []
    assert _product_site_queries("random weather athens") == []

    vercel_hosts = _detect_product_sites("Vercel pricing")
    assert any("vercel.com" in h for h in vercel_hosts)


def test_site_aware_path_merges_official_hits(monkeypatch, tmp_path):
    from executor import internet_search_engine

    monkeypatch.setattr(internet_search_engine, "_ddg_instant", lambda query: [])
    monkeypatch.setattr(internet_search_engine, "_wikipedia_search", lambda query: [])
    monkeypatch.setattr(internet_search_engine, "CACHE", tmp_path / "cache.json")

    def fake_html(query, limit=5):
        if "site:render.com" in query or "site:docs.render.com" in query:
            return [{
                "title": "Free Instance Types",
                "url": "https://render.com/docs/free",
                "snippet": "Render free tier for web services",
                "source": "ddg_html",
            }]
        return [{
            "title": "Shiny - Wikipedia",
            "url": "https://en.wikipedia.org/wiki/Shiny",
            "snippet": "R package",
            "source": "ddg_html",
        }]

    monkeypatch.setattr(internet_search_engine, "_ddg_html", fake_html)

    result = internet_search_engine.search_web("Render free tier", limit=5)

    assert result["ok"] is True
    assert result.get("site_aware") is True
    urls = [r.get("url", "") for r in result.get("results", [])]
    assert any("render.com" in u for u in urls)
    assert result.get("low_relevance") is False
