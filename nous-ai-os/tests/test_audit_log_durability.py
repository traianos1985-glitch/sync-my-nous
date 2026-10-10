from concurrent.futures import ThreadPoolExecutor
import importlib
import json
from pathlib import Path

import pytest

from executor import action_log, agent_journal


def test_concurrent_action_log_writes_are_not_lost(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module = importlib.reload(action_log)
    monkeypatch.setattr(module, "FILE", "data/action_log.json")

    with ThreadPoolExecutor(max_workers=10) as pool:
        list(pool.map(lambda index: module.log_action("test", {"index": index}), range(80)))

    persisted = json.loads(Path("data/action_log.json").read_text(encoding="utf-8"))
    assert len(persisted) == 80
    assert {entry["result"]["index"] for entry in persisted} == set(range(80))
    assert Path("data/action_log.json.lock").exists()


def test_concurrent_journal_writes_preserve_hash_chain(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module = importlib.reload(agent_journal)
    monkeypatch.setattr(module, "FILE", "data/agent_journal.json")

    with ThreadPoolExecutor(max_workers=10) as pool:
        list(pool.map(lambda index: module.write_journal("parallel", {"index": index}), range(80)))

    persisted = json.loads(Path("data/agent_journal.json").read_text(encoding="utf-8"))
    assert len(persisted) == 80
    assert module.verify_journal() == {"ok": True, "entries": 80}
    assert Path("data/agent_journal.json.lock").exists()


def test_journal_verification_works_after_retention_and_detects_tampering(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module = importlib.reload(agent_journal)
    monkeypatch.setattr(module, "FILE", "data/agent_journal.json")

    for index in range(module.MAX_ENTRIES + 3):
        module.write_journal("retention", {"index": index})

    assert module.verify_journal() == {"ok": True, "entries": module.MAX_ENTRIES}
    persisted = json.loads(Path("data/agent_journal.json").read_text(encoding="utf-8"))
    persisted[10]["data"]["index"] = "tampered"
    Path("data/agent_journal.json").write_text(json.dumps(persisted), encoding="utf-8")
    assert module.verify_journal()["error"] == "journal_integrity_failed"


def test_corrupt_journal_is_reported_and_never_overwritten(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module = importlib.reload(agent_journal)
    monkeypatch.setattr(module, "FILE", "data/agent_journal.json")
    Path("data").mkdir()
    original = b'{"truncated":'

    Path("data/agent_journal.json").write_bytes(original)

    integrity = module.verify_journal()
    with pytest.raises(RuntimeError, match="journal_integrity_failure"):
        module.write_journal("must_not_erase_history", {"safe": True})

    assert integrity["ok"] is False
    assert integrity["error"] == "journal_store_integrity_failure"
    assert Path("data/agent_journal.json").read_bytes() == original


def test_malformed_journal_records_and_broken_hash_chain_fail_closed(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module = importlib.reload(agent_journal)
    monkeypatch.setattr(module, "FILE", "data/agent_journal.json")
    Path("data").mkdir()
    original = json.dumps([{"event": "partial"}, "malformed"]).encode("utf-8")
    Path("data/agent_journal.json").write_bytes(original)

    assert module.verify_journal()["error"] == "journal_store_integrity_failure"
    with pytest.raises(RuntimeError, match="journal_integrity_failure"):
        module.write_journal("must_not_erase_history")

    assert Path("data/agent_journal.json").read_bytes() == original

    Path("data/agent_journal.json").write_text("[]", encoding="utf-8")
    module.write_journal("valid")
    persisted = json.loads(Path("data/agent_journal.json").read_text(encoding="utf-8"))
    persisted[0]["event"] = "tampered"
    tampered = json.dumps(persisted).encode("utf-8")
    Path("data/agent_journal.json").write_bytes(tampered)

    assert module.verify_journal()["error"] == "journal_integrity_failed"
    with pytest.raises(RuntimeError, match="journal_integrity_failure"):
        module.write_journal("must_not_extend_tampered_chain")
    assert Path("data/agent_journal.json").read_bytes() == tampered
