"""Admin authorization contracts for globally shared memory and autonomous state."""

import pytest

pytest.importorskip("flask")


@pytest.mark.parametrize(
    ("method", "route", "body"),
    [
        ("get", "/remote/conversations", None),
        ("get", "/remote/conversations/123456789", None),
        ("post", "/remote/conversations/search", {"query": "private"}),
        ("post", "/remote/conversations/123456789/rename", {"title": "renamed"}),
        ("delete", "/remote/conversations/123456789", None),
        ("post", "/remote/conversations/123456789/auto-title", {}),
        ("post", "/remote/conversations/auto-title", {"limit": 1}),
        ("post", "/remote/autonomous-repair/approve", {"proposal_id": "1"}),
        ("post", "/remote/autonomous-repair/reject", {"proposal_id": "1"}),
        ("post", "/remote/goal-manager-v2/generate", {}),
        ("post", "/remote/goal-manager-v2/update-progress", {}),
        ("post", "/remote/upgrade-planner/propose", {}),
        ("post", "/remote/upgrade-planner/approve", {"plan_id": "1"}),
        ("post", "/remote/upgrade-planner/reject", {"plan_id": "1"}),
        ("post", "/remote/goals-v2/refresh", {"id": "1"}),
        ("post", "/remote/technical-sources/propose-upgrades", {"limit": 1}),
        ("post", "/remote/app-builder/plan", {"description": "test"}),
    ],
)
def test_shared_state_and_autonomous_routes_require_admin(
    monkeypatch, method, route, body
):
    from executor import router

    monkeypatch.setenv("NOUS_TOKEN", "shared-state-admin-boundary-master-token")
    monkeypatch.setattr(router, "check_admin_token", lambda _request: False)

    # Any side-effecting or costly handler must stop at the authorization
    # boundary, before it can reach a storage, research or model operation.
    for name in (
        "approve_repair_proposal",
        "reject_repair_proposal",
        "generate_projects_from_goals",
        "update_project_progress",
        "propose_upgrade_plan",
        "approve_upgrade_plan",
        "reject_upgrade_plan",
        "refresh_goal_progress",
        "refresh_goal_progress_by_id",
        "propose_release_evidence_plans",
        "plan_app",
        "list_conversations",
        "get_conversation",
        "rename_conversation",
        "delete_conversation",
        "search_conversations",
        "generate_conversation_title",
        "auto_title_recent_conversations",
    ):
        if hasattr(router, name):
            monkeypatch.setattr(
                router,
                name,
                lambda *args, _name=name, **kwargs: pytest.fail(
                    f"{_name} ran before admin authorization"
                ),
            )

    client = router.app.test_client()
    response = getattr(client, method)(
        route,
        json=body,
        headers={
            "Authorization": "Bearer shared-state-admin-boundary-master-token"
        },
    )

    assert response.status_code == 401
    assert response.get_json()["error"] == "unauthorized"
