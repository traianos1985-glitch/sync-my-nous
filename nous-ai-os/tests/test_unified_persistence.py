import importlib
import json
import sqlite3
from pathlib import Path
import pytest
from executor import mission_system, task_queue, unified_persistence


def test_unified_database_retains_missions_and_queue_after_reload(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(mission_system, "FILE", "data/missions.json")
    monkeypatch.setattr(task_queue, "FILE", "data/agent_queue.json")
    mission = mission_system.create_mission("durable")
    task = task_queue.add_task("durable task")
    importlib.reload(mission_system)
    importlib.reload(task_queue)
    assert mission_system.list_missions()[0]["id"] == mission["id"]
    assert task_queue.list_queue()[0]["id"] == task["id"]
    with sqlite3.connect("data/nous_storage.db") as conn:
        assert conn.execute("SELECT count(*) FROM runtime_snapshots").fetchone()[0] == 2


def test_migration_once_retains_legacy_backup(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("data").mkdir()
    old = '[{"id":"legacy","tasks":[]}]'
    Path("data/missions.json").write_text(old)
    with unified_persistence.transaction("data/missions.json", "mission_store_integrity_failure"):
        items = unified_persistence.load("data/missions.json")
        items.append({"id": "new", "tasks": []})
        unified_persistence.save("data/missions.json", items)
    assert Path("data/missions.json").read_text() == old
    with unified_persistence.transaction("data/missions.json", "mission_store_integrity_failure"):
        assert [item["id"] for item in unified_persistence.load("data/missions.json")] == ["legacy", "new"]


def test_claims_and_snapshot_commit_atomically(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = "data/missions.json"
    with unified_persistence.transaction(path, "mission_store_integrity_failure"):
        unified_persistence.save(path, [{"id": "m", "tasks": [{"id": "t", "execution_id": "claim", "status": "running", "started": 12}]}])
    with pytest.raises(ValueError):
        with unified_persistence.transaction(path, "mission_store_integrity_failure"):
            unified_persistence.save(path, [])
            raise ValueError("rollback")
    with sqlite3.connect("data/nous_storage.db") as conn:
        assert conn.execute("SELECT execution_id,status FROM task_claims").fetchone() == ("claim", "running")
        assert json.loads(conn.execute("SELECT data FROM runtime_snapshots").fetchone()[0])[0]["id"] == "m"