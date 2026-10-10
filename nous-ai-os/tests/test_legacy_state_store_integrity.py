import importlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from executor import decision_memory, learning_memory, task_state


@pytest.mark.parametrize("module_name,file_name,operation", [
    ("decision_memory", "decision_memory.json", "decision"),
    ("learning_memory", "lessons_learned.json", "lesson"),
    ("task_state", "tasks.json", "task"),
])
@pytest.mark.parametrize("raw", [b'{"broken":', b'{"not":"a list"}', b'[{"valid":true}, 7]'])
def test_legacy_state_stores_fail_closed_without_overwrite(tmp_path, monkeypatch, module_name, file_name, operation, raw):
    monkeypatch.chdir(tmp_path)
    module = importlib.reload({"decision_memory": decision_memory, "learning_memory": learning_memory, "task_state": task_state}[module_name])
    monkeypatch.setattr(module, "FILE", f"data/{file_name}")
    Path("data").mkdir()
    path = Path("data") / file_name
    path.write_bytes(raw)

    with pytest.raises(RuntimeError, match="json_state_integrity_failure"):
        if operation == "decision":
            module.record_decision("must preserve data")
        elif operation == "lesson":
            module.record_lesson("must preserve data")
        else:
            module.add_task("must preserve data")
    assert path.read_bytes() == raw


def test_concurrent_task_state_writes_are_not_lost(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module = importlib.reload(task_state)
    monkeypatch.setattr(module, "FILE", "data/tasks.json")
    with ThreadPoolExecutor(max_workers=8) as pool:
        created = list(pool.map(module.add_task, [f"task-{i}" for i in range(40)]))
    stored = json.loads(Path("data/tasks.json").read_text(encoding="utf-8"))
    assert len(created) == len(stored) == 40
    assert len({item["id"] for item in stored}) == 40


def test_valid_legacy_stores_use_atomic_locked_persistence(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    dm = importlib.reload(decision_memory)
    lm = importlib.reload(learning_memory)
    ts = importlib.reload(task_state)
    monkeypatch.setattr(dm, "FILE", "data/decision_memory.json")
    monkeypatch.setattr(lm, "FILE", "data/lessons_learned.json")
    monkeypatch.setattr(ts, "FILE", "data/tasks.json")

    assert dm.record_decision("decision")["title"] == "decision"
    assert lm.record_lesson("lesson")["lesson"] == "lesson"
    task = ts.add_task("task")
    assert ts.close_task(task["id"])[0]["status"] == "closed"
    assert Path("data/tasks.json.lock").exists()
