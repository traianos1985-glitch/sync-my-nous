import pytest

pytest.importorskip("flask")


def _master_header(monkeypatch):
    token = "larmor-route-admin-boundary-master-token"
    monkeypatch.setenv("NOUS_TOKEN", token)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize(
    ("route", "body"),
    [
        ("/larmor/analyze", {"session_data": "data", "question": "analyze"}),
        ("/larmor/chat", {"conversation": [{"role": "user", "content": "hello"}]}),
    ],
)
def test_larmor_model_routes_require_admin(monkeypatch, route, body):
    from executor import router

    headers = _master_header(monkeypatch)
    monkeypatch.setattr(router, "check_admin_token", lambda _request: False)
    monkeypatch.setattr(
        router,
        "analyze_session",
        lambda *_args, **_kwargs: pytest.fail("analysis must not run"),
    )
    monkeypatch.setattr(
        router,
        "larmor_chat",
        lambda *_args, **_kwargs: pytest.fail("chat model must not run"),
    )

    response = router.app.test_client().post(route, json=body, headers=headers)

    assert response.status_code == 401
    assert response.get_json()["error"] == "unauthorized"


def test_larmor_analysis_rejects_oversized_input_before_provider_call(monkeypatch):
    from executor import router

    headers = _master_header(monkeypatch)
    monkeypatch.setattr(router, "check_admin_token", lambda _request: True)
    monkeypatch.setattr(
        router,
        "analyze_session",
        lambda *_args, **_kwargs: pytest.fail("oversized analysis must not run"),
    )

    response = router.app.test_client().post(
        "/larmor/analyze",
        json={"session_data": "x" * 12001, "question": "test"},
        headers=headers,
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "session_data_too_long"


def test_larmor_chat_rejects_excessive_turns_before_provider_call(monkeypatch):
    from executor import router

    headers = _master_header(monkeypatch)
    monkeypatch.setattr(router, "check_admin_token", lambda _request: True)
    monkeypatch.setattr(
        router,
        "larmor_chat",
        lambda *_args, **_kwargs: pytest.fail("oversized chat must not run"),
    )

    response = router.app.test_client().post(
        "/larmor/chat",
        json={
            "conversation": [
                {"role": "user", "content": "x"} for _ in range(21)
            ]
        },
        headers=headers,
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "conversation_too_long"


def test_larmor_model_routes_still_work_for_admin(monkeypatch):
    from executor import router

    headers = _master_header(monkeypatch)
    monkeypatch.setattr(router, "check_admin_token", lambda _request: True)
    monkeypatch.setattr(router, "analyze_session", lambda *_args, **_kwargs: "analysis-ok")
    monkeypatch.setattr(router, "larmor_chat", lambda *_args, **_kwargs: "reply-ok")

    client = router.app.test_client()
    analysis = client.post(
        "/larmor/analyze",
        json={"session_data": "bounded data", "question": "test"},
        headers=headers,
    )
    chat = client.post(
        "/larmor/chat",
        json={"conversation": [{"role": "user", "content": "hello"}]},
        headers=headers,
    )

    assert analysis.status_code == 200
    assert analysis.get_json()["analysis"] == "analysis-ok"
    assert chat.status_code == 200
    assert chat.get_json()["reply"] == "reply-ok"
