import sys
import types


def _module(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    return module


def test_component_hides_exception_details():
    from executor.runtime_diagnostics import _component

    result = _component("secret-bearing-check", lambda: (_ for _ in ()).throw(RuntimeError("token=do-not-leak")))

    assert result == {
        "name": "secret-bearing-check",
        "status": "unavailable",
        "error": "RuntimeError",
    }
    assert "do-not-leak" not in repr(result)


def test_queue_check_tolerates_malformed_items_and_redacts_store_details(monkeypatch):
    from executor import runtime_diagnostics

    monkeypatch.setitem(
        sys.modules,
        "executor.task_queue",
        _module(
            "executor.task_queue",
            inspect_queue_store=lambda: {
                "status": "healthy",
                "path": "/private/path",
                "token": "do-not-leak",
            },
            list_queue=lambda: [
                {"status": "pending"},
                None,
                {"status": "running", "started": "not-a-timestamp"},
            ],
        ),
    )

    result = runtime_diagnostics._queue_check()

    assert result["status"] == "degraded"
    assert result["counts"]["pending"] == 1
    assert result["counts"]["other"] == 1
    assert result["malformed_items"] == 1
    assert result["stale_running"] == 1
    assert result["store_integrity"] == {"status": "healthy"}
    assert "do-not-leak" not in repr(result)
    assert "/private/path" not in repr(result)


def test_queue_check_caps_scan_and_marks_truncated(monkeypatch):
    from executor import runtime_diagnostics

    monkeypatch.setitem(
        sys.modules,
        "executor.task_queue",
        _module(
            "executor.task_queue",
            inspect_queue_store=lambda: {"status": "healthy"},
            list_queue=lambda: [{"status": "done"}] * 2001,
        ),
    )

    result = runtime_diagnostics._queue_check()

    assert result["truncated"] is True
    assert result["scanned_items"] == 2000
    assert result["status"] == "degraded"
    assert result["counts"]["done"] == 2000


def test_mission_check_normalizes_bad_counts_and_redacts_integrity(monkeypatch):
    from executor import runtime_diagnostics

    monkeypatch.setitem(
        sys.modules,
        "executor.mission_system",
        _module(
            "executor.mission_system",
            mission_status=lambda: {
                "total": "bad",
                "active": -3,
                "done": 2,
                "blocked": "0",
                "private": "should-not-escape",
            },
            list_missions=lambda: [],
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "executor.mission_integrity",
        _module(
            "executor.mission_integrity",
            audit_missions=lambda _missions: {
                "ok": True,
                "checked": 2,
                "private_path": "/private/path",
            },
        ),
    )

    result = runtime_diagnostics._mission_check()

    assert result["status"] == "healthy"
    assert result["counts"] == {"total": 0, "active": 0, "done": 2, "blocked": 0}
    assert result["integrity"] == {"ok": True, "checked": 2}
    assert "should-not-escape" not in repr(result)
    assert "/private/path" not in repr(result)


def test_journal_check_returns_only_integrity_summary(monkeypatch):
    from executor import runtime_diagnostics

    monkeypatch.setitem(
        sys.modules,
        "executor.agent_journal",
        _module(
            "executor.agent_journal",
            verify_journal=lambda: {
                "ok": False,
                "entries_checked": 4,
                "secret_event": "do-not-leak",
                "path": "/private/path",
            },
        ),
    )

    result = runtime_diagnostics._journal_check()

    assert result == {
        "status": "degraded",
        "integrity": {"ok": False, "entries_checked": 4},
    }
    assert "do-not-leak" not in repr(result)
    assert "/private/path" not in repr(result)
