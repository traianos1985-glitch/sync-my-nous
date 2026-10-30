import pytest

from executor.research_broker import ResearchSource, format_context, research_status, validate_url


def _public_dns(*_args, **_kwargs):
    return [(None, None, None, None, ("93.184.216.34", 443))]


def test_blocks_private_and_unsupported_urls(monkeypatch):
    monkeypatch.setattr("executor.research_broker.socket.getaddrinfo", _public_dns)
    for url in ("http://127.0.0.1:5000/health", "http://localhost", "http://192.168.1.2/admin", "file:///tmp/x"):
        with pytest.raises(ValueError):
            validate_url(url)


def test_official_domain_allowlist(monkeypatch):
    monkeypatch.setattr("executor.research_broker.socket.getaddrinfo", _public_dns)
    assert validate_url("https://docs.python.org/3/", {"docs.python.org"}).startswith("https://docs.python.org")
    with pytest.raises(ValueError, match="domain_not_allowed"):
        validate_url("https://example.com", {"docs.python.org"})


def test_unresolved_or_empty_dns_fails_closed(monkeypatch):
    monkeypatch.setattr("executor.research_broker.socket.getaddrinfo", lambda *_a, **_k: [])
    with pytest.raises(ValueError, match="host_resolution_failed"):
        validate_url("https://docs.python.org")
    monkeypatch.setattr("executor.research_broker.socket.getaddrinfo", lambda *_a, **_k: [(None, None, None, None, ("10.0.0.8", 443))])
    with pytest.raises(ValueError, match="private_address"):
        validate_url("https://docs.python.org")


def test_rejects_credentials_and_unusual_ports(monkeypatch):
    monkeypatch.setattr("executor.research_broker.socket.getaddrinfo", _public_dns)
    with pytest.raises(ValueError, match="url_credentials_not_allowed"):
        validate_url("https://user:secret@example.com")
    with pytest.raises(ValueError, match="port_not_allowed"):
        validate_url("https://example.com:8443")


def test_context_is_bounded_and_auditable():
    sources = [ResearchSource("Docs", "https://docs.python.org", "x" * 7000)]
    result = research_status(sources, "deep")
    assert result["used"] is True
    assert result["source_count"] == 1
    assert len(result["context"]) <= 12000
    assert format_context(sources).startswith("[Source 1]")
