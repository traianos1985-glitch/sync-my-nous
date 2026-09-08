from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.cwd()
DATA = ROOT / "data"
REPORTS = DATA / "reports"
ARCHIVE = DATA / "archive"

MISSIONS = DATA / "missions.json"
LESSONS = DATA / "lessons_learned.json"
KNOWLEDGE = DATA / "knowledge_queue.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def task_statuses(mission: dict[str, Any]) -> list[str]:
    tasks = mission.get("tasks", [])
    if not isinstance(tasks, list):
        return []
    return [
        str(t.get("status", "")).lower().strip()
        for t in tasks
        if isinstance(t, dict)
    ]


def add_lesson(mission: dict[str, Any]) -> None:
    lessons = load_json(LESSONS, [])
    if not isinstance(lessons, list):
        lessons = []

    mid = mission.get("id")
    for item in lessons:
        if isinstance(item, dict) and item.get("source_mission_id") == mid:
            return

    lessons.append({
        "id": int(datetime.now().timestamp() * 1000000),
        "created_at": now_iso(),
        "source": "mission_lifecycle_manager",
        "source_mission_id": mid,
        "title": f"Mission completed: {mission.get('title')}",
        "lesson": "Mission reached terminal/completed state and was archived by lifecycle manager.",
        "success": True,
    })
    save_json(LESSONS, lessons)


def add_knowledge(mission: dict[str, Any]) -> None:
    queue = load_json(KNOWLEDGE, [])
    if not isinstance(queue, list):
        queue = []

    mid = mission.get("id")
    for item in queue:
        if isinstance(item, dict) and item.get("source_mission_id") == mid:
            return

    queue.append({
        "id": int(datetime.now().timestamp() * 1000000),
        "created_at": now_iso(),
        "source": "mission_lifecycle_manager",
        "source_mission_id": mid,
        "kind": "mission_lifecycle",
        "title": mission.get("title"),
        "status": mission.get("status"),
        "summary": "Mission archived and converted into knowledge queue item.",
    })
    save_json(KNOWLEDGE, queue)


def run_mission_lifecycle_manager() -> dict[str, Any]:
    REPORTS.mkdir(parents=True, exist_ok=True)
    ARCHIVE.mkdir(parents=True, exist_ok=True)

    missions = load_json(MISSIONS, [])
    if not isinstance(missions, list):
        missions = []

    active = []
    archived = []
    changed = False

    for mission in missions:
        if not isinstance(mission, dict):
            active.append(mission)
            continue

        status = str(mission.get("status", "")).lower().strip()
        statuses = task_statuses(mission)

        terminal = status in {"completed", "done", "cancelled", "archived"}
        all_done = bool(statuses) and all(s in {"done", "completed"} for s in statuses)

        if terminal or all_done:
            mission["status"] = "completed" if all_done and status not in {"cancelled"} else mission.get("status", "completed")
            mission["archived_at"] = mission.get("archived_at") or now_iso()
            archived.append(mission)
            add_lesson(mission)
            add_knowledge(mission)
            changed = True
        else:
            active.append(mission)

    if archived:
        archive_path = ARCHIVE / f"mission_lifecycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        save_json(archive_path, archived)
        save_json(MISSIONS, active)

    report = {
        "tool": "Mission Lifecycle Manager",
        "timestamp": now_iso(),
        "before": len(missions),
        "active_after": len(active),
        "archived": len(archived),
        "changed": changed,
    }

    report_path = REPORTS / f"mission_lifecycle_manager_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_json(report_path, report)
    report["report_path"] = str(report_path)
    return report


if __name__ == "__main__":
    print(json.dumps(run_mission_lifecycle_manager(), indent=2, ensure_ascii=False))
