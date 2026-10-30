from executor import safe_outbound_http as safe


class FakeResponse:
    def __init__(self, status=200, body=b"ok", headers=None):
        self.status = status
        self._body = body
        self._headers = headers or {"Content-Type": "text/plain; charset=utf-8"}

    def getheaders(self):
        return list(self._headers.items())

    def getheader(self, name):
        return self._headers.get(name)

    def read(self, _size=-1):
        body, self._body = self._body, b""
        return body

    def close(self):
        pass


class FakeConnection:
    seen = []

    def __init__(self, host, port, hostname=None, timeout=None):
        self.host = host
        self.port = port
        self.response = FakeResponse()
        self.__class__.seen.append(self)

    def request(self, method, path, headers):
        self.method = method
        self.path = path
        self.headers = headers

    def getresponse(self):
        return self.response

    def close(self):
        pass


def test_rejects_private_and_mixed_dns_answers(monkeypatch):
    monkeypatch.setattr(
        safe.socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [
            (safe.socket.AF_INET, safe.socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443)),
            (safe.socket.AF_INET, safe.socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443)),
        ],
    )
    result = safe.fetch_public_http("https://public-looking.example/")
    assert result["ok"] is False
    assert result["error"] == "invalid_or_non_public_url"


def test_rejects_localhost_credentials_and_unusual_ports():
    assert safe.fetch_public_http("http://127.0.0.1/")["error"] == "invalid_or_non_public_url"
    assert safe.fetch_public_http("http://localhost/")["error"] == "non_public_host"
    assert safe.fetch_public_http("https://user:pass@example.com/")["error"] == "url_credentials_not_allowed"
    assert safe.fetch_public_http("https://example.com:8443/")["error"] == "invalid_or_non_public_url"


def test_connects_to_validated_ip_and_preserves_original_host_header(monkeypatch):
    FakeConnection.seen.clear()
    monkeypatch.setattr(safe, "_resolve_public_addresses", lambda _host, _port: ["8.8.8.8"])
    monkeypatch.setattr(safe, "_PinnedHTTPSConnection", FakeConnection)
    result = safe.fetch_public_http("https://research.example/path?q=1")

    assert result["ok"] is True
    connection = FakeConnection.seen[-1]
    assert connection.host == "8.8.8.8"
    assert connection.method == "GET"
    assert connection.path == "/path?q=1"
    assert connection.headers["Host"] == "research.example"
    assert result["connected_ip"] == "8.8.8.8"


def test_redirects_are_rejected_not_followed(monkeypatch):
    monkeypatch.setattr(safe, "_resolve_public_addresses", lambda _host, _port: ["8.8.8.8"])
    monkeypatch.setattr(safe, "_PinnedHTTPSConnection", FakeConnection)
    FakeConnection.seen.clear()
    FakeConnection.seen_response = FakeResponse(
        status=302, headers={"Location": "http://127.0.0.1/admin"}
    )
    original_init = FakeConnection.__init__

    def redirect_init(self, host, port, hostname=None, timeout=None):
        original_init(self, host, port, hostname, timeout)
        self.response = FakeConnection.seen_response

    monkeypatch.setattr(FakeConnection, "__init__", redirect_init)
    result = safe.fetch_public_http("https://research.example/redirect")
    assert result["ok"] is False
    assert result["error"] == "redirect_blocked"
    assert result["status"] == 302


def test_response_size_is_bounded(monkeypatch):
    monkeypatch.setattr(safe, "_resolve_public_addresses", lambda _host, _port: ["8.8.8.8"])
    monkeypatch.setattr(safe, "_PinnedHTTPSConnection", FakeConnection)
    original_init = FakeConnection.__init__

    def large_init(self, host, port, hostname=None, timeout=None):
        original_init(self, host, port, hostname, timeout)
        self.response = FakeResponse(body=b"x" * 1024)

    monkeypatch.setattr(FakeConnection, "__init__", large_init)
    result = safe.fetch_public_http("https://research.example/large", max_bytes=100)
    assert result["ok"] is False
    assert result["error"] == "response_too_large"
