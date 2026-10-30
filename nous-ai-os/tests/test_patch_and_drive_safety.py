from pathlib import Path
import threading

import pytest

from executor import nous_drive, patch_apply_engine, patch_generator


def test_patch_proposal_does_not_claim_success_for_unsupported_target(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(patch_generator, "PROPOSAL_FILE", "data/patch_proposals.json")
    proposal = {
        "id": "unsupported-1",
        "status": "pending",
        "can_apply": True,
        "patches": [{
            "path": "executor/another_module.py",
            "apply_strategy": "replace_file",
            "diff": "--- before\n+++ after\n",
        }],
    }
    patch_generator._save([proposal])

    result = patch_generator.approve_patch_proposal("unsupported-1")

    assert result["ok"] is False
    assert result["proposal"]["status"] == "unsupported_strategy"
    assert result["proposal"]["result"]["applied"] == []
    assert result["proposal"]["result"]["unsupported"][0]["reason"] == "unsupported_target"
    assert "runtime filesystem only" not in result["proposal"]["result"]["note"]


def test_patch_apply_history_records_unsupported_without_false_rollback(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(patch_generator, "PROPOSAL_FILE", "data/patch_proposals.json")
    monkeypatch.setattr(patch_apply_engine, "FILE", "data/patch_apply_history.json")
    patch_generator._save([{
        "id": "unsupported-2",
        "status": "pending",
        "can_apply": True,
        "patches": [{
            "path": "executor/not_supported.py",
            "apply_strategy": "replace_file",
        }],
    }])

    result = patch_apply_engine.apply_patch_proposal("unsupported-2")

    assert result["ok"] is False
    assert result["event"]["status"] == "unsupported_strategy"
    assert "rollback_after_failure" not in result["event"]
    assert result["event"]["persistence"] == "none"
    assert patch_apply_engine.list_patch_apply_history()[0]["status"] == "unsupported_strategy"


def test_patch_state_loaders_fail_closed_on_corrupt_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(patch_generator, "PROPOSAL_FILE", "data/patch_proposals.json")
    monkeypatch.setattr(patch_apply_engine, "FILE", "data/patch_apply_history.json")
    Path("data").mkdir()
    Path("data/patch_proposals.json").write_text("{truncated", encoding="utf-8")
    Path("data/patch_apply_history.json").write_text("{truncated", encoding="utf-8")

    with pytest.raises(RuntimeError, match="json_state_integrity_failure"):
        patch_generator._load()
    with pytest.raises(RuntimeError, match="json_state_integrity_failure"):
        patch_apply_engine._load()


def test_drive_proposal_can_only_be_approved_once(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(nous_drive, "DRIVE_FILE", Path("data/nous_drive.json"))
    state = {
        "proposals": [{
            "id": "drive-1",
            "action": "self_reflection",
            "fingerprint": "reflection-1",
            "status": "pending",
        }],
        "last_think": 0,
        "think_count": 0,
        "drive_log": [],
    }
    Path("data").mkdir()\n    nous_drive._save(state)

    starts = []

    class FakeThread:
        def __init__(self, *args, **kwargs):
            pass

        def start(self):
            starts.append(True)

    monkeypatch.setattr(threading, "Thread", FakeThread)

    first = nous_drive.approve_proposal("drive-1")
    second = nous_drive.approve_proposal("drive-1")

    assert first["ok"] is True
    assert first["executing"] is True
    assert second["ok"] is False
    assert second["error"] == "proposal_not_pending"
    assert second["status"] == "executing"
    assert len(starts) == 1
    assert nous_drive.get_proposal("drive-1")["status"] == "executing"
