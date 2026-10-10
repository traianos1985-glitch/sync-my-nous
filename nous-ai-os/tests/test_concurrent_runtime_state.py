from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

import pytest

from executor import operator_approval, task_queue


def test_concurrent_queue_writes_do_not_lose_tasks(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(task_queue, "FILE", "data/agent_queue.json")
    with ThreadPoolExecutor(max_workers=12) as pool:
        created = list(pool.map(lambda index: task_queue.add_task(f"task-{index}"), range(60)))

    persisted = json.loads(Path("data/agent_queue.json").read_text(encoding="utf-8"))
    assert len(created) == 60
    assert len(persisted) == 60
    assert len({str(item["id"]) for item in persisted}) == 60


def test_approval_state_file_uses_atomic_sidecar_locked_updates(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(operator_approval, "FILE", "data/operator_approvals.json")

    approval = operator_approval.request_approval("deploy", {"target": "staging"})
    assert operator_approval.approve(approval["id"])["status"] == "approved"
    assert operator_approval.claim_approved_approval(
        approval["id"], "deploy", {"target": "staging"}
    )["status"] == "executing"
    assert operator_approval.finish_approval(approval["id"], "completed", {"ok": True})["status"] == "completed"
    assert Path("data/operator_approvals.json.lock").exists()
    assert json.loads(Path("data/operator_approvals.json").read_text(encoding="utf-8"))[0]["status"] == "completed"


def test_approval_rejects_invalid_payload_and_nonterminal_finish_status(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(operator_approval, "FILE", str(tmp_path / "approvals.json"))
    with pytest.raises(ValueError, match="payload_must_be_object"):
        operator_approval.request_approval("deploy", ["not", "an", "object"])

    approval = operator_approval.request_approval("deploy", {"target": "staging"})
    operator_approval.approve(approval["id"])
    operator_approval.claim_approved_approval(approval["id"], "deploy", {"target": "staging"})
    with pytest.raises(ValueError, match="invalid_final_approval_status"):
        operator_approval.finish_approval(approval["id"], "approved")
