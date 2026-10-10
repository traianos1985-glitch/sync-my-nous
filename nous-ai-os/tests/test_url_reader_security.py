from __future__ import annotations

from executor import url_reader_engine


def test_reader_rejects_localhost_before_network(monkeypatch):
    def unexpected_request(*args, **kwargs):
        raise AssertionError("network must not be called for localhost")

    monkeypatch.setattr("requests.get", unexpected_request)
    result = url_reader_engine.read_url("http://localhost/admin")

    assert result["ok"] is False
    assert result["error"] == "non_public_host"


def test_reader_rejects_non_http_schemes():
    result = url_reader_engine.read_url("file:///etc/passwd")

    assert result["ok"] is False
    assert result["error"] == "unsupported_scheme"


def test_reader_blocks_redirects(monkeypatch):
    class FakeResponse:
        status_code = 302
        headers = {"Location": "http://127.0.0.1/"}

        def close(self):
            self.closed = True

    monkeypatch.setattr(url_reader_engine, "_validate_public_http_url", lambda url: (True, None))
    monkeypatch.setattr("requests.get", lambda *args, **kwargs: FakeResponse())

    result = url_reader_engine.read_url("https://public.example/redirect")

    assert result["ok"] is False
    assert result["error"] == "redirect_blocked"


def test_reader_rejects_invalid_text_limit():
    result = url_reader_engine.read_url("https://example.com", limit=0)

    assert result["ok"] is False
    assert result["error"] == "invalid_text_limit"
