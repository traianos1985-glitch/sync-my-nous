"""Regression tests for chat/mission GitHub, Larmor and field tools plus failure recovery."""
import pytest

from executor import chat_tools, failure_memory, mission_actions, ops_console


@pytest.fixture(autouse=True)
def isolated_failures(monkeypatch, tmp_path):
    monkeypatch.setattr(failure_memory, "FAILURE_MEMORY_FILE", str(tmp_path / "failures.json"))
    yield


def test_larmor_mission_action_matches_formula():
    result = mission_actions.run_mission_action("larmor_calculate", {"material": "cu", "b_field_tesla": 48.23e-6})
    assert result["ok"] is True
    # gamma(63Cu)=11.3114e6 Hz/T -> 11.3114e6 * 48.23e-6 = 545.549 Hz
    assert abs(result["result"]["harmonics"][0]["hz"] - 545.549) < 0.01


def test_larmor_rejects_non_positive_field_and_unknown_material():
    assert mission_actions.run_mission_action("larmor_calculate", {"material": "cu", "b_field_tesla": 0})["error"] == "invalid_b_field_tesla"
    bad = mission_actions.run_mission_action("larmor_calculate", {"material": "nope", "b_field_tesla": 1e-5})
    assert bad["ok"] is False and bad["error"] == "unknown_material"


def test_field_log_saves_and_reads_back(monkeypatch, tmp_path):
    from executor import field_engine
    monkeypatch.setattr(field_engine, "ENTRIES_FILE", tmp_path / "entries.json")
    monkeypatch.setattr(field_engine, "FIELD_DIR", tmp_path)
    result = mission_actions.run_mission_action("field_log", {"title": "Δοκιμή", "note": "χωρίς εκσκαφή"})
    assert result["ok"] is True and result["verified"] is True
    assert "unverified" in result["entry"]["tags"]


def test_field_log_requires_paired_coordinates():
    result = mission_actions.run_mission_action("field_log", {"title": "x", "lat": 38.0})
    assert result["error"] == "coordinates_must_be_paired"


def test_github_writes_need_approval_in_missions_and_ops():
    from executor import mission_system
    assert {"github_commit", "github_deploy_pages"} <= mission_system.APPROVAL_REQUIRED
    assert "github_commit" not in mission_actions.AUTO_SAFE_ACTIONS
    blocked = ops_console.run_ops_action("github_commit", {"owner": "a", "repo": "b", "path": "c", "content": "d", "message": "e"})
    assert blocked["error"] == "approval_required"


def test_github_commit_verifies_by_reading_back(monkeypatch):
    from executor import github_operator as gh
    monkeypatch.setattr(gh, "get_file_content", lambda *a, **k: {"ok": True, "sha": "s", "content": "old"})
    monkeypatch.setattr(gh, "commit_file", lambda *a, **k: {"ok": True})
    result = mission_actions.action_github_commit({"owner": "a", "repo": "b", "path": "c", "content": "new", "message": "m"})
    assert result["ok"] is False and result["error"] == "commit_verification_failed"


def test_known_persistent_failure_is_not_retried(monkeypatch):
    from executor import github_operator as gh
    calls = []
    monkeypatch.setattr(gh, "get_repository_tree", lambda *a, **k: calls.append(1) or {"ok": False, "error": "missing_token"})
    first = mission_actions.run_mission_action("github_read", {"owner": "a", "repo": "b"})
    assert first["error"] == "missing_token" and len(calls) == 1  # persistent error: no retry
    second = mission_actions.run_mission_action("github_read", {"owner": "a", "repo": "b"})
    assert second["error"] == "known_failure_avoided" and second["previous_error"] == "missing_token"
    assert len(calls) == 1
    assert "Πρόσθεσε GitHub token" in (second["suggested_fix"] or "")


def test_transient_read_failure_retried_once(monkeypatch):
    from executor import github_operator as gh
    results = iter([{"ok": False, "error": "github_http_502"}, {"ok": True, "items": []}])
    monkeypatch.setattr(gh, "get_repository_tree", lambda *a, **k: next(results))
    result = mission_actions.run_mission_action("github_read", {"owner": "a", "repo": "b"})
    assert result["ok"] is True and result["retried"] is True


def test_chat_larmor_and_field_tools_execute(monkeypatch, tmp_path):
    from executor import field_engine
    monkeypatch.setattr(field_engine, "ENTRIES_FILE", tmp_path / "entries.json")
    monkeypatch.setattr(field_engine, "FIELD_DIR", tmp_path)
    larmor = chat_tools.execute_call("larmor_calculate", {"material": "cu", "b_field_tesla": "0,00004823"})
    assert larmor["status"] == "completed" and larmor["executed"] is True
    log = chat_tools.execute_call("field_log", {"title": "Σημείο Α", "note": "παρατήρηση"})
    assert log["status"] == "completed"


def test_chat_commit_request_creates_approval_mission_without_committing(monkeypatch):
    from executor import github_operator as gh, mission_system
    monkeypatch.setattr(gh, "commit_file", lambda *a, **k: pytest.fail("chat must never commit"))
    created = {}
    monkeypatch.setattr(mission_system, "create_mission",
                        lambda title, description="", tasks=None: created.update(tasks=tasks) or {"id": 7, "tasks": tasks})
    record = chat_tools.execute_call("github_commit_request",
                                     {"owner": "a", "repo": "b", "path": "README.md", "content": "hi", "message": "docs"})
    assert record["status"] == "completed"
    assert record["output"]["committed"] is False and record["output"]["status"] == "waiting_approval"
    assert created["tasks"][0]["action"] == "github_commit"


def test_chat_failure_is_recorded_and_then_avoided(monkeypatch):
    from executor import github_operator as gh
    monkeypatch.setattr(gh, "get_github_status", lambda: {"ok": False, "error": "missing_token"})
    assert chat_tools.execute_call("github_status", {})["status"] == "failed"
    again = chat_tools.execute_call("github_status", {})
    assert again["status"] == "blocked" and again["error"].startswith("known_failure_avoided")
    assert "github_status" in failure_memory.failure_hints("chat_tools", ["github_status"])
