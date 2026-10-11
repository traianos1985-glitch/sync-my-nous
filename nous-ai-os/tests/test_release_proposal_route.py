from executor import auth_guard, router


PATH = "/remote/technical-sources/propose-upgrades"


def _authenticate(monkeypatch, allowed=True):
    # The app-level guard and the route both enforce authentication.
    monkeypatch.setattr(auth_guard, "check_token", lambda request: allowed)
    monkeypatch.setattr(router, "check_token", lambda request: allowed)


def test_release_proposal_route_rejects_unauthenticated_requests(monkeypatch):
    _authenticate(monkeypatch, allowed=False)
    monkeypatch.setattr(
        router,
        "propose_release_evidence_plans",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("must not be called")),
    )

    response = router.app.test_client().post(PATH, json={"limit": 5})

    assert response.status_code == 401
    assert response.get_json()["error"] == "unauthorized"


def test_release_proposal_route_rejects_non_object_json(monkeypatch):
    _authenticate(monkeypatch, allowed=True)
    monkeypatch.setattr(
        router,
        "propose_release_evidence_plans",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("must not be called")),
    )

    response = router.app.test_client().post(PATH, json=["not", "an", "object"])

    assert response.status_code == 400
    assert response.get_json() == {"ok": False, "error": "invalid_request_body"}


def test_release_proposal_route_passes_valid_limit_and_returns_result(monkeypatch):
    _authenticate(monkeypatch, allowed=True)
    calls = []

    def fake_propose_release_evidence_plans(*, limit):
        calls.append(limit)
        return {"ok": True, "created_count": 2, "plans": []}

    monkeypatch.setattr(router, "propose_release_evidence_plans", fake_propose_release_evidence_plans)

    response = router.app.test_client().post(PATH, json={"limit": 3})

    assert response.status_code == 200
    assert response.get_json()["created_count"] == 2
    assert calls == [3]
