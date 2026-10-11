import json
from pathlib import Path

import pytest

from executor import scheduler_cron


def isolate_schedule(tmp_path, monkeypatch):
    path = tmp_path / "data" / "scheduler_cron.json"
    monkeypatch.setattr(scheduler_cron, "SCHEDULE_FILE", path)
    return path


def test_cron_rejects_actions_that_could_auto_approve_risky_proposals(tmp_path, monkeypatch):
    path = isolate_schedule(tmp_path, monkeypatch)

    for action in ("cleanup_disk", "restore_data_files", "implement_capability", "github_sync", "arbitrary_action"):
        result = scheduler_cron.add_job("unsafe", action, 9, 0)
        assert result == {"ok": False, "error": "action_not_allowlisted"}

    assert not path.exists()


def test_cron_accepts_only_bounded_time_and_day_values(tmp_path, monkeypatch):
    isolate_schedule(tmp_path, monkeypatch)

    assert scheduler_cron.add_job("bad-hour", "create_backup", 24, 0)["error"] == "invalid_schedule_time"
    assert scheduler_cron.add_job("bad-minute", "create_backup", 9, 60)["error"] == "invalid_schedule_time"
    assert scheduler_cron.add_job("bad-days", "create_backup", 9, 0, ["monday"])["error"] == "invalid_schedule_days"
    assert scheduler_cron.add_job("valid", "create_backup", 9, 15, ["mon", "fri"])["action"] == "create_backup"


def test_cron_never_executes_or_approves_a_non_allowlisted_action(monkeypatch):
    import executor.nous_drive as drive

    monkeypatch.setattr(drive, "think", lambda **_kwargs: (_ for _ in ()).throw(AssertionError("must not think")))
    monkeypatch.setattr(drive, "approve_proposal", lambda *_args: (_ for _ in ()).throw(AssertionError("must not approve")))
    monkeypatch.setattr(drive, "list_proposals", lambda: [{"id": "danger", "action": "cleanup_disk", "status": "pending"}])

    assert scheduler_cron._execute_job({"action": "cleanup_disk"}) == {
        "ok": False,
        "error": "action_not_allowlisted",
    }


def test_corrupt_cron_state_is_preserved_and_mutations_fail_closed(tmp_path, monkeypatch):
    path = isolate_schedule(tmp_path, monkeypatch)
    path.parent.mkdir(parents=True)
    original = b'{"jobs":'
    path.write_bytes(original)

    with pytest.raises(ValueError, match="schedule_store_unavailable"):
        scheduler_cron.add_job("backup", "create_backup", 9, 0)
    assert scheduler_cron.cron_status()["error"] == "schedule_store_unavailable"
    assert path.read_bytes() == original


def test_cron_state_save_is_atomic_and_leaves_no_temp_files(tmp_path, monkeypatch):
    path = isolate_schedule(tmp_path, monkeypatch)

    created = scheduler_cron.add_job("backup", "create_backup", 9, 0)
    assert created["action"] == "create_backup"
    assert json.loads(path.read_text(encoding="utf-8"))["jobs"]
    assert list(path.parent.glob(".scheduler-cron-*.tmp")) == []


@pytest.mark.parametrize("route", [
    "/remote/self-diagnosis/ai-analyze",
    "/remote/workspace/create-mission",
    "/remote/nous-drive/think",
    "/remote/knowledge/remember",
    "/nous/cron/add",
    "/nous/cron/remove",
    "/nous/cron/toggle",
    "/upload",
    "/upload-image",
    "/remote/document/upload",
])
def test_sensitive_router_mutations_require_admin_token(monkeypatch, route):
    from executor import router

    monkeypatch.setenv("NOUS_TOKEN", "route-auth-test-master")
    monkeypatch.setattr(router, "check_admin_token", lambda _request: False)
    response = router.app.test_client().post(
        route,
        json={"name": "backup", "action": "create_backup", "hour": 9, "minute": 0},
        headers={"Authorization": "Bearer route-auth-test-master"},
    )

    assert response.status_code == 401
    assert response.get_json()["error"] == "unauthorized"


def test_dashboard_knowledge_upload_requires_admin_scope(monkeypatch):
    from executor import dashboard_api, router

    monkeypatch.setenv("NOUS_TOKEN", "route-auth-test-master")
    monkeypatch.setattr(dashboard_api, "check_admin_token", lambda _request: False)
    response = router.app.test_client().post(
        "/api/knowledge",
        headers={"Authorization": "Bearer route-auth-test-master"},
    )

    assert response.status_code == 401
    assert response.get_json()["error"] == "unauthorized"
