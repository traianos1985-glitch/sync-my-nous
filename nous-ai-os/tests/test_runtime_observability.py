import json
import time
from pathlib import Path


def test_diagnostics_reports_component_failure_without_hiding_other_checks(tmp_path, monkeypatch):
    import importlib
    from executor import runtime_diagnostics, task_queue, mission_system, agent_journal

    monkeypatch.chdir(tmp_path)
    queue = importlib.reload(task_queue)
    journal = importlib.reload(agent_journal)
    missions = importlib.reload(mission_system)
    diagnostics = importlib.reload(runtime_diagnostics)

    queue.add_task("failed task")
    task = queue.next_task()
    queue.update_task(task["id"], status="failed", finished=time.time(), last_error="expected test failure")
    journal.write_journal("test_event", {"safe": True})
    report = diagnostics.collect_diagnostics()

    assert report["status"] == "degraded"
    components = {item["name"]: item for item in report["components"]}
    assert components["task_queue"]["status"] == "degraded"
    assert components["audit_journal"]["status"] == "healthy"
    assert components["disk"]["status"] in {"healthy", "degraded"}
    assert report["summary"]["total"] == 4


def test_diagnostics_detects_tampered_audit_journal(tmp_path, monkeypatch):
    import importlib
    from executor import agent_journal, runtime_diagnostics

    monkeypatch.chdir(tmp_path)
    journal = importlib.reload(agent_journal)
    diagnostics = importlib.reload(runtime_diagnostics)
    journal.write_journal("first", {"value": 1})
    journal.write_journal("second", {"value": 2})
    entries = json.loads(Path("data/agent_journal.json").read_text(encoding="utf-8"))
    entries[1]["data"]["value"] = 999
    Path("data/agent_journal.json").write_text(json.dumps(entries), encoding="utf-8")

    report = diagnostics.collect_diagnostics()
    components = {item["name"]: item for item in report["components"]}
    assert components["audit_journal"]["status"] == "degraded"
    assert report["ok"] is False


def test_metrics_persistence_is_atomic_and_collector_errors_are_visible(tmp_path, monkeypatch):
    import importlib
    from executor import runtime_metrics

    monkeypatch.chdir(tmp_path)
    metrics = importlib.reload(runtime_metrics)
    metrics.FILE = "data/runtime_metrics.json"
    monkeypatch.setattr(metrics, "list_queue", lambda: [{"status": "pending"}])
    monkeypatch.setattr(metrics, "project_summary", lambda: {"total": 2})
    monkeypatch.setattr(metrics, "service_status", lambda: {"enabled": True})
    monkeypatch.setattr(metrics, "list_schedules", lambda: (_ for _ in ()).throw(RuntimeError("scheduler offline")))
    monkeypatch.setattr(metrics, "battery_guard", lambda: {"ok": True})

    result = metrics.collect_metrics()
    saved = json.loads(Path("data/runtime_metrics.json").read_text(encoding="utf-8"))

    assert result["status"] == "degraded"
    assert "scheduler" in result["component_errors"]["schedules"]
    assert saved["queue"]["pending"] == 1
    assert not list(Path("data").glob(".runtime_metrics.*.tmp"))


def test_diagnostics_detects_corrupt_queue_json_instead_of_reporting_empty_healthy_queue(tmp_path, monkeypatch):
    import importlib
    from executor import runtime_diagnostics, task_queue

    monkeypatch.chdir(tmp_path)
    queue = importlib.reload(task_queue)
    diagnostics = importlib.reload(runtime_diagnostics)
    Path("data").mkdir()
    Path("data/agent_queue.json").write_text("{not valid json", encoding="utf-8")

    report = diagnostics.collect_diagnostics()
    component = next(item for item in report["components"] if item["name"] == "task_queue")

    assert queue.list_queue() == []
    assert component["status"] == "degraded"
    assert component["store_integrity"]["status"] == "degraded"
    assert component["store_integrity"]["error"].startswith("queue_store_unreadable:")
    assert report["ok"] is False


def test_diagnostics_counts_malformed_queue_records_without_crashing(tmp_path, monkeypatch):
    import importlib
    from executor import runtime_diagnostics, task_queue

    monkeypatch.chdir(tmp_path)
    queue = importlib.reload(task_queue)
    diagnostics = importlib.reload(runtime_diagnostics)
    Path("data").mkdir()
    Path("data/agent_queue.json").write_text(
        json.dumps([{"id": 1, "status": "pending", "priority": 1}, ["malformed"], None]),
        encoding="utf-8",
    )

    report = diagnostics.collect_diagnostics()
    component = next(item for item in report["components"] if item["name"] == "task_queue")

    assert len(queue.list_queue()) == 1
    assert component["status"] == "degraded"
    assert component["store_integrity"]["record_count"] == 3
    assert component["store_integrity"]["malformed_records"] == 2
    assert report["ok"] is False
