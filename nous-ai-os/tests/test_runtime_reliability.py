import json
import os
import time
from pathlib import Path


def test_queue_save_is_valid_and_stale_recovery_is_bounded(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import importlib
    from executor import task_queue

    queue = importlib.reload(task_queue)
    queue.add_task("stale", priority=2)
    queue.update_task(queue.next_task()["id"], status="running", started=time.time() - 1000)
    first = queue.recover_dead_tasks(max_age_seconds=1, max_recoveries=1)
    assert len(first["recovered"]) == 1
    assert first["recovered"][0]["recovery_count"] == 1
    assert first["recovered"][0]["status"] == "pending"

    task = queue.next_task()
    queue.update_task(task["id"], status="running", started=time.time() - 1000)
    second = queue.recover_dead_tasks(max_age_seconds=1, max_recoveries=1)
    assert second["recovered"] == []
    assert len(second["failed"]) == 1
    assert second["failed"][0]["status"] == "failed"
    assert second["failed"][0]["last_error"] == "stale_running_recovery_limit_exceeded"

    persisted = json.loads(Path("data/agent_queue.json").read_text(encoding="utf-8"))
    assert persisted[0]["status"] == "failed"


def test_queue_handles_invalid_top_level_json_shape_and_attempt_values(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import importlib
    from executor import task_queue

    queue = importlib.reload(task_queue)
    Path("data").mkdir()
    Path("data/agent_queue.json").write_text('{"not": "a list"}', encoding="utf-8")
    assert queue.list_queue() == []
    assert queue.retry_failed(max_attempts=0)["error"] == "max_attempts_must_be_positive"


def test_rollback_rejects_paths_outside_workspace(tmp_path, monkeypatch):
    import importlib
    from executor import rollback_engine

    monkeypatch.chdir(tmp_path)
    engine = importlib.reload(rollback_engine)
    outside = tmp_path.parent / "outside-secret.txt"
    outside.write_text("do not overwrite", encoding="utf-8")

    result = engine.backup_file(outside)
    assert result["ok"] is False
    assert result["error"] == "unsafe_or_missing_source"


def test_rollback_backup_and_restore_are_confined_to_workspace(tmp_path, monkeypatch):
    import importlib
    from executor import rollback_engine

    monkeypatch.chdir(tmp_path)
    engine = importlib.reload(rollback_engine)
    target = Path("workspace.txt")
    target.write_text("original", encoding="utf-8")

    backup = engine.backup_file(target)
    assert backup["ok"] is True
    target.write_text("changed", encoding="utf-8")

    result = engine.rollback_backup(backup["backup"]["id"])
    assert result["ok"] is True
    assert target.read_text(encoding="utf-8") == "original"

    # A tampered history entry cannot direct rollback outside the repository.
    history = json.loads(Path(engine.FILE).read_text(encoding="utf-8"))
    history[0]["source"] = str(tmp_path.parent / "outside-secret.txt")
    Path(engine.FILE).write_text(json.dumps(history), encoding="utf-8")
    denied = engine.rollback_backup(backup["backup"]["id"])
    assert denied["ok"] is False
    assert denied["error"] == "unsafe_rollback_destination"


def test_mission_lifecycle_does_not_record_cancelled_mission_as_success(tmp_path, monkeypatch):
    import importlib
    from executor import mission_lifecycle_manager as lifecycle

    monkeypatch.chdir(tmp_path)
    lifecycle = importlib.reload(lifecycle)
    lifecycle.DATA = Path("data")
    lifecycle.REPORTS = lifecycle.DATA / "reports"
    lifecycle.ARCHIVE = lifecycle.DATA / "archive"
    lifecycle.MISSIONS = lifecycle.DATA / "missions.json"
    lifecycle.LESSONS = lifecycle.DATA / "lessons_learned.json"
    lifecycle.KNOWLEDGE = lifecycle.DATA / "knowledge_queue.json"
    lifecycle.MISSIONS.parent.mkdir(parents=True)
    lifecycle.MISSIONS.write_text(
        json.dumps([{"id": "cancelled-1", "title": "Cancelled task", "status": "cancelled", "tasks": []}]),
        encoding="utf-8",
    )

    result = lifecycle.run_mission_lifecycle_manager()
    lessons = json.loads(lifecycle.LESSONS.read_text(encoding="utf-8"))
    assert result["archived"] == 1
    assert lessons[0]["success"] is False
    assert lessons[0]["outcome"] == "cancelled"
