import importlib
import json
from pathlib import Path

import pytest

from executor.runtime_governance import (
    ActionPayloadError,
    result_succeeded,
    safe_payload_summary,
    validate_action_payload,
)


def test_payload_requires_json_object_and_rejects_unsupported_values():
    with pytest.raises(ActionPayloadError, match="payload_must_be_object"):
        validate_action_payload(["not", "an", "object"])
    with pytest.raises(ActionPayloadError, match="payload_must_be_json_compatible"):
        validate_action_payload({"bad": object()})


def test_payload_limits_depth_size_and_non_finite_numbers():
    with pytest.raises(ActionPayloadError, match="payload_too_deep"):
        payload = {"leaf": 1}
        for _ in range(9):
            payload = {"nested": payload}
        validate_action_payload(payload)
    with pytest.raises(ActionPayloadError, match="payload_string_too_long"):
        validate_action_payload({"value": "x" * 9000})
    with pytest.raises(ActionPayloadError, match="payload_non_finite_number"):
        validate_action_payload({"value": float("nan")})


def test_payload_summary_never_copies_secret_values():
    summary = safe_payload_summary({"api_key": "super-secret-value", "count": 3})
    assert summary["keys"] == ["api_key", "count"]
    assert summary["types"]["api_key"] == "string"
    assert "super-secret-value" not in json.dumps(summary)


def test_result_success_requires_no_explicit_failure():
    assert result_succeeded({"ok": True, "result": {"ok": True}}) is True
    assert result_succeeded({"ok": True, "result": {"ok": False}}) is False
    assert result_succeeded({"ok": False}) is False
    assert result_succeeded("not a result object") is False


def test_real_action_gate_has_explicit_allowlist_and_truthful_result(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from executor import real_action_gate as gate

    gate = importlib.reload(gate)
    monkeypatch.setattr(gate, "reality_status", lambda: {
        "internet": {"real": True},
        "browser_read": {"real": True},
        "android": {"real_intents": True, "real_gestures": False},
        "git": {"real": True},
        "code": {"real": True},
        "app_factory": {"real": True},
    })
    monkeypatch.setattr(gate, "code_health", lambda: {"ok": False, "error": "test_failure"})
    monkeypatch.setattr(gate, "write_journal", lambda *_a, **_k: {"ok": True})

    unknown = gate.run_real_action("time", {})
    failed = gate.run_real_action("code_health", {"api_key": "secret-value"})

    assert unknown["ok"] is False
    assert unknown["error"] == "unknown_action"
    assert failed["ok"] is False
    assert failed["result"]["error"] == "test_failure"
    assert "secret-value" not in json.dumps(failed)
    assert failed["payload_summary"]["types"]["api_key"] == "string"


def test_real_action_gate_rejects_non_object_payload():
    from executor import real_action_gate as gate

    result = gate.run_real_action("code_health", ["unexpected"])
    assert result == {"ok": False, "error": "payload_must_be_object", "action": "code_health"}


def test_mission_store_corruption_is_not_silently_reset(tmp_path, monkeypatch):
    from executor import mission_system

    monkeypatch.chdir(tmp_path)
    module = importlib.reload(mission_system)
    Path("data").mkdir()
    original = b'{"truncated":'
    Path(module.FILE).write_bytes(original)

    with pytest.raises(RuntimeError, match="mission_store_integrity_failure"):
        module.list_missions()
    with pytest.raises(RuntimeError, match="mission_store_integrity_failure"):
        module.create_mission("must not overwrite history")
    assert Path(module.FILE).read_bytes() == original
