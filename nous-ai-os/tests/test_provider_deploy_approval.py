import pytest
from executor import operator_approval, router


def test_provider_deployment_requires_single_use_operator_approval(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(operator_approval, "FILE", str(tmp_path / "operator_approvals.json"))
    monkeypatch.setattr(router, "check_admin_token", lambda _request: True)
    calls = []
    payload = {"provider": "vercel", "path": str(tmp_path / "project")}
    monkeypatch.setattr(
        router,
        "prepare_provider_deploy",
        lambda _provider, _path: {"ok": True, "payload": payload},
    )
    monkeypatch.setattr(
        router,
        "execute_provider_deploy",
        lambda approved_payload: calls.append(approved_payload) or {
            "ok": True, "provider": approved_payload["provider"], "exit_code": 0
        },
    )
    (tmp_path / "project").mkdir()
    client = router.app.test_client()

    requested = client.post(
        "/remote/deploy/provider-run",
        json={"provider": "vercel", "path": "."},
    )
    assert requested.status_code == 202
    assert requested.get_json()["approval_required"] is True
    assert calls == []

    approval_id = requested.get_json()["approval_id"]
    approved = client.post(
        "/remote/operator/approve-provider-deploy",
        json={"id": approval_id},
    )
    assert approved.status_code == 200
    assert approved.get_json()["ok"] is True
    assert calls == [payload]
    assert operator_approval.get_approval(approval_id)["status"] == "completed"

    replayed = client.post(
        "/remote/operator/approve-provider-deploy",
        json={"id": approval_id},
    )
    assert replayed.status_code == 409
    assert len(calls) == 1


def test_provider_deploy_rejects_non_object_body_before_creating_approval(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(operator_approval, "FILE", str(tmp_path / "operator_approvals.json"))
    monkeypatch.setattr(router, "check_admin_token", lambda _request: True)
    client = router.app.test_client()

    response = client.post(
        "/remote/deploy/provider-run",
        data="[]",
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "json_object_required"
    assert operator_approval.list_approvals() == []



def test_legacy_vercel_route_also_requires_approval(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(operator_approval, "FILE", str(tmp_path / "operator_approvals.json"))
    monkeypatch.setattr(router, "check_admin_token", lambda _request: True)
    payload = {"provider": "vercel", "path": str(tmp_path / "project"), "mode": "production"}
    monkeypatch.setattr(
        router,
        "prepare_provider_deploy",
        lambda *_args: {"ok": True, "payload": payload},
    )
    monkeypatch.setattr(
        router,
        "execute_provider_deploy",
        lambda *_args: pytest.fail("deployment must not run before operator approval"),
    )
    (tmp_path / "project").mkdir()
    client = router.app.test_client()

    response = client.post("/remote/vercel/deploy", json={"path": ".", "prod": True})

    assert response.status_code == 202
    assert response.get_json()["approval_required"] is True
    assert operator_approval.list_approvals(status="pending")[0]["action"] == "provider_deploy"
