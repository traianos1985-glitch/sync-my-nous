"""User-scoped tokens must not read shared private memory or generated artifacts."""

import pytest

pytest.importorskip("flask")


@pytest.mark.parametrize(
    "route",
    [
        "/remote/agent/proposals",
        "/remote/agent/decide",
        "/remote/agent/goals",
        "/remote/agent/journal",
        "/remote/lessons/list",
        "/remote/decision-memory/list",
        "/remote/knowledge/queue",
        "/remote/knowledge/base",
        "/remote/brain/state",
        "/remote/brain/load",
        "/remote/brain-backup/list",
        "/remote/queue",
        "/remote/projects",
        "/remote/projects/summary",
        "/remote/goals-v2",
        "/remote/missions",
        "/remote/missions/approvals",
        "/remote/mission-planner/proposals",
        "/remote/autonomous-repair/proposals",
        "/remote/patch-generator/proposals",
        "/remote/upgrade-planner/plans",
        "/remote/operator/approvals",
        "/remote/nous-drive/proposals",
        "/remote/app-builder/files",
        "/remote/app-builder/list",
        "/remote/app-builder/get/plan_123",
        "/remote/app-builder/app-log",
        "/remote/app-builder/download/sample_app",
        "/remote/self-improve/patches",
        "/remote/code-analyst/reports",
        "/remote/deep-code-analyst/reports",
    ],
)
def test_shared_private_state_reads_require_admin(monkeypatch, route):
    from executor import router

    token = "shared-private-read-boundary-master-token"
    monkeypatch.setenv("NOUS_TOKEN", token)
    monkeypatch.setattr(router, "check_admin_token", lambda _request: False)

    response = router.app.test_client().get(
        route,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.get_json()["error"] == "unauthorized"
