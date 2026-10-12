import json
from urllib.error import URLError

from executor.runtime_verification import _base_url, verify_runtime


class FakeResponse:
    def __init__(self, payload, status=200):
        self.status = status
        self._raw = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, limit):
        assert limit <= 64 * 1024 + 1
        return self._raw[:limit]


def test_base_url_requires_https_and_rejects_credentials_or_query():
    assert _base_url("https://example.com/base/") == "https://example.com/base"
    for value in (
        "http://example.com",
        "https://user:secret@example.com",
        "https://example.com?token=secret",
        "https://example.com/#fragment",
        "not-a-url",
    ):
        try:
            _base_url(value)
        except ValueError as exc:
            assert str(exc) == "invalid_healthcheck_url"
        else:
            raise AssertionError(f"URL should be rejected: {value}")


def test_verifier_checks_liveness_and_readiness_with_bounded_requests():
    requests = []

    def opener(request, timeout):
        requests.append((request.full_url, timeout, dict(request.header_items())))
        if request.full_url.endswith("/api/system/health"):
            return FakeResponse({"status": "healthy", "kind": "liveness"})
        return FakeResponse({"ok": True, "components": []})

    result = verify_runtime("https://nous.example", opener=opener)
    assert result["ok"] is True
    assert result["mode"] == "single_post_deploy_probe"
    assert result["remote_state_changed"] is False
    assert [item[0] for item in requests] == [
        "https://nous.example/api/system/health",
        "https://nous.example/api/system/ready",
    ]
    assert all(timeout == 8 for _, timeout, _ in requests)
    assert all("Authorization" not in headers for _, _, headers in requests)


def test_verifier_fails_if_readiness_is_degraded():
    def opener(request, timeout):
        if request.full_url.endswith("/health"):
            return FakeResponse({"status": "healthy", "kind": "liveness"})
        return FakeResponse({"ok": False}, status=503)

    result = verify_runtime("https://nous.example", opener=opener)
    assert result["ok"] is False
    assert result["checks"][0]["ok"] is True
    assert result["checks"][1]["ok"] is False
    assert result["checks"][1]["status_code"] == 503


def test_verifier_redacts_transport_error_and_does_not_retry():
    calls = []

    def opener(request, timeout):
        calls.append(request.full_url)
        raise URLError("contains-private-path-and-credentials")

    result = verify_runtime("https://nous.example", opener=opener)
    assert result["ok"] is False
    assert len(calls) == 2
    assert "contains-private-path-and-credentials" not in repr(result)


def test_invalid_url_fails_closed_without_network_call():
    def opener(*args, **kwargs):
        raise AssertionError("network must not be called for invalid URL")

    result = verify_runtime("http://localhost:5000", opener=opener)
    assert result == {"ok": False, "error": "invalid_healthcheck_url", "checks": []}
