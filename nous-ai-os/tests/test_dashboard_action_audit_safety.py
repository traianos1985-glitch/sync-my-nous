from types import SimpleNamespace

from executor import dashboard_action_audit as audit


def test_dashboard_audit_never_dispatches_mutating_actions(monkeypatch):
    actions = [
        {"name": "read", "method": "GET", "path": "/status", "auth": False},
        {"name": "mutate", "method": "POST", "path": "/run", "auth": True},
    ]
    called = []

    def fake_run_action(_app, action, _headers):
        called.append(action["name"])
        return SimpleNamespace(
            status_code=200,
            is_json=True,
            get_json=lambda: {"ok": True},
        )

    monkeypatch.setattr(audit, "ACTIONS", actions)
    monkeypatch.setattr(audit, "_run_action", fake_run_action)

    result = audit.dashboard_action_audit(object(), token="owner-token")

    assert called == ["read"]
    assert result["ok"] is True
    assert result["passed"] == 1
    assert result["failed"] == 0
    assert result["skipped"] == 1
    skipped = next(item for item in result["results"] if item["name"] == "mutate")
    assert skipped["skipped"] is True
    assert skipped["error"] == "skipped_non_read_only"


def test_dashboard_audit_counts_get_failures_but_not_skipped_posts(monkeypatch):
    actions = [
        {"name": "read-fails", "method": "GET", "path": "/status", "auth": False},
        {"name": "mutate", "method": "POST", "path": "/run", "auth": True},
    ]
    monkeypatch.setattr(audit, "ACTIONS", actions)
    monkeypatch.setattr(
        audit,
        "_run_action",
        lambda *_args: SimpleNamespace(
            status_code=503,
            is_json=True,
            get_json=lambda: {"error": "unavailable"},
        ),
    )

    result = audit.dashboard_action_audit(object())

    assert result["ok"] is False
    assert result["passed"] == 0
    assert result["failed"] == 1
    assert result["skipped"] == 1
