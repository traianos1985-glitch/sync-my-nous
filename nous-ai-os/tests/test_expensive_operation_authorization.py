import pytest


pytest.importorskip("flask")


@pytest.mark.parametrize("route", [
    "/api/gemini-check",
    "/gemini-check",
    "/remote/executive/plan",
    "/remote/quality-gate/run",
])
def test_expensive_model_and_quality_routes_require_admin(monkeypatch, route):
    from executor import router

    monkeypatch.setenv("NOUS_TOKEN", "expensive-route-master-token")
    monkeypatch.setattr(router, "check_admin_token", lambda _request: False)
    response = router.app.test_client().post(
        route,
        json={"prompt": "test", "label": "test"},
        headers={"Authorization": "Bearer expensive-route-master-token"},
    )

    assert response.status_code == 401
    assert response.get_json()["error"] == "unauthorized"


def test_gemini_check_bounds_prompt_before_provider_call(monkeypatch):
    from executor import router

    monkeypatch.setenv("NOUS_TOKEN", "expensive-route-master-token")
    monkeypatch.setattr(router, "check_admin_token", lambda _request: True)
    monkeypatch.setattr(
        router,
        "check_gemini",
        lambda *_args, **_kwargs: pytest.fail("oversized prompt must not call Gemini"),
    )
    response = router.app.test_client().post(
        "/api/gemini-check",
        json={"prompt": "x" * 501},
        headers={"Authorization": "Bearer expensive-route-master-token"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "prompt_too_long"


def test_executive_plan_requires_a_bounded_prompt(monkeypatch):
    from executor import router

    monkeypatch.setenv("NOUS_TOKEN", "expensive-route-master-token")
    monkeypatch.setattr(router, "check_admin_token", lambda _request: True)
    monkeypatch.setattr(
        router,
        "executive_plan",
        lambda *_args, **_kwargs: pytest.fail("empty prompt must not run planner"),
    )
    response = router.app.test_client().post(
        "/remote/executive/plan",
        json={"prompt": " "},
        headers={"Authorization": "Bearer expensive-route-master-token"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "prompt_empty_or_too_long"


def test_quality_gate_rejects_malformed_file_list_before_running(monkeypatch):
    from executor import router

    monkeypatch.setenv("NOUS_TOKEN", "expensive-route-master-token")
    monkeypatch.setattr(router, "check_admin_token", lambda _request: True)
    monkeypatch.setattr(
        router,
        "quality_gate",
        lambda *_args, **_kwargs: pytest.fail("malformed file list must not run checks"),
    )
    response = router.app.test_client().post(
        "/remote/quality-gate/run",
        json={"files": "router.py"},
        headers={"Authorization": "Bearer expensive-route-master-token"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "invalid_files_list"
