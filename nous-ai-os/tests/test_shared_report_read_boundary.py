"""Private reports and shared project records require admin authorization."""

import pytest

pytest.importorskip("flask")


@pytest.mark.parametrize(
    "route",
    [
        "/remote/goals/progress",
        "/remote/goals/summary",
        "/remote/patch-apply/history",
        "/remote/rollback/history",
        "/remote/cleanup/reports",
        "/remote/goal-manager-v2/projects",
        "/remote/executive-intelligence/report",
        "/remote/technical-intelligence/report",
        "/remote/technical-intelligence/proposals",
        "/remote/technical-sources/report",
        "/remote/research/learned",
        "/field/list",
        "/larmor/history",
        "/remote/project-health",
    ],
)
def test_shared_reports_and_persistent_records_require_admin(monkeypatch, route):
    from executor import router

    token = "shared-report-read-boundary-master-token"
    monkeypatch.setenv("NOUS_TOKEN", token)
    monkeypatch.setattr(router, "check_admin_token", lambda _request: False)

    response = router.app.test_client().get(
        route,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.get_json()["error"] == "unauthorized"
