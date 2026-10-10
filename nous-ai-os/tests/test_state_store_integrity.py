import importlib
from pathlib import Path
import pytest

from executor import action_log, operator_approval


@pytest.mark.parametrize("raw", [
    b'{"truncated":',
    b'{"not":"a list"}',
    b'[{"id": 1, "status": "pending"}, "broken"]',
    b'[{"id": 1, "status": "pending"}, {"id": 1, "status": "approved"}]',
])
def test_corrupt_approval_store_fails_closed(tmp_path, monkeypatch, raw):
    monkeypatch.chdir(tmp_path)
    module = importlib.reload(operator_approval)
    monkeypatch.setattr(module, "FILE", "data/operator_approvals.json")
    Path("data").mkdir()
    path = Path("data/operator_approvals.json")
    path.write_bytes(raw)

    with pytest.raises(RuntimeError, match="approval_store_integrity_failure"):
        module.request_approval("deploy")
    with pytest.raises(RuntimeError, match="approval_store_integrity_failure"):
        module.approve(1)
    assert path.read_bytes() == raw


@pytest.mark.parametrize("raw", [b'{"truncated":', b'{"not":"a list"}', b'[{"action":"ok"}, 7]'])
def test_corrupt_action_log_fails_closed(tmp_path, monkeypatch, raw):
    monkeypatch.chdir(tmp_path)
    module = importlib.reload(action_log)
    monkeypatch.setattr(module, "FILE", "data/action_log.json")
    Path("data").mkdir()
    path = Path("data/action_log.json")
    path.write_bytes(raw)

    with pytest.raises(RuntimeError, match="action_log_integrity_failure"):
        module.log_action("test")
    with pytest.raises(RuntimeError, match="action_log_integrity_failure"):
        module.recent_actions()
    assert path.read_bytes() == raw


def test_valid_approval_and_action_log_stores_still_work(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    approvals = importlib.reload(operator_approval)
    actions = importlib.reload(action_log)
    monkeypatch.setattr(approvals, "FILE", "data/operator_approvals.json")
    monkeypatch.setattr(actions, "FILE", "data/action_log.json")

    approval = approvals.request_approval("deploy", {"environment": "test"})
    assert approvals.approve(approval["id"])["status"] == "approved"
    assert approvals.get_approval(approval["id"])["status"] == "approved"
    actions.log_action("test", {"ok": True})
    assert actions.recent_actions()[0]["result"] == {"ok": True}
