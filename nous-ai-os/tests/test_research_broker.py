import pytest

from executor.research_broker import ResearchSource, format_context, research_status, validate_url


def test_blocks_private_and_unsupported_urls(monkeypatch):
    monkeypatch.setattr("executor.research_broker.socket.getaddrinfo", lambda *args, **kwargs: [])
    for url in ("http://127.0.0.1:5000/health", "http://localhost", "file:///tmp/x"):
        with pytest.raises(ValueError):
            validate_url(url)


def test_official_domain_allowlist(monkeypatch):
    monkeypatch.setattr("executor.research_broker.socket.getaddrinfo", lambda *args, **kwargs: [])
    assert validate_url("https://docs.python.org/3/", {"docs.python.org"}).startswith("https://docs.python.org")
    with pytest.raises(ValueError):
        validate_url("https://example.com", {"docs.python.org"})


def test_context_is_bounded_and_auditable():
    sources = [ResearchSource("Docs", "https://docs.python.org", "x" * 7000)]
    result = research_status(sources, "deep")
    assert result["used"] is True
    assert result["source_count"] == 1
    assert len(result["context"]) <= 12000
    assert format_context(sources).startswith("[Source 1]")
