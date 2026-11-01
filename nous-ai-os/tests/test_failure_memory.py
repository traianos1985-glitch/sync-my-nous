"""Tests for Failure Memory & Recovery Registry."""
import pytest
from executor import failure_memory
from executor.router import app

@pytest.fixture(autouse=True)
def clean_memory(tmp_path, monkeypatch):
    test_file = tmp_path / "failure_memory.json"
    monkeypatch.setattr(failure_memory, "FAILURE_MEMORY_FILE", str(test_file))
    failure_memory.clear_failure_memory()
    yield
    failure_memory.clear_failure_memory()

def test_record_and_query_failure():
    entry = failure_memory.record_failure(
        domain="browser",
        action="read_url",
        error="SSRFProtectionError",
        details={"url": "http://127.0.0.1"},
        suggested_fix="Use public HTTP(S) URL only"
    )
    assert entry["domain"] == "browser"
    assert entry["action"] == "read_url"
    assert entry["occurrences"] == 1

    results = failure_memory.query_failures(domain="browser")
    assert len(results) == 1
    assert results[0]["error"] == "SSRFProtectionError"

def test_deduplication_increments_count():
    failure_memory.record_failure("browser", "read_url", "TimeoutError")
    second = failure_memory.record_failure("browser", "read_url", "TimeoutError")
    assert second["occurrences"] == 2

    results = failure_memory.query_failures(domain="browser")
    assert len(results) == 1
    assert results[0]["occurrences"] == 2

def test_router_failure_memory_endpoints(monkeypatch):
    client = app.test_client()
    res = client.get("/remote/failure-memory/list")
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert isinstance(data["failures"], list)

    # Unauthorized POST
    post_res = client.post("/remote/failure-memory/record", json={"domain": "test", "action": "run", "error": "failed"})
    assert post_res.status_code == 401

    # Authorized POST
    monkeypatch.setenv("NOUS_TOKEN", "valid-token")
    auth_res = client.post(
        "/remote/failure-memory/record",
        headers={"X-NOUS-TOKEN": "valid-token"},
        json={"domain": "test", "action": "run", "error": "failed"}
    )
    assert auth_res.status_code == 200
    assert auth_res.get_json()["ok"] is True
