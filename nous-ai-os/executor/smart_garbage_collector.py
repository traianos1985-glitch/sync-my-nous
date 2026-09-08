from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.cwd()
DATA = ROOT / "data"
REPORTS = DATA / "reports"
ARCHIVE = DATA / "archive"

KEEP_LAST_BRAIN_BACKUPS = 20

FILES_TO_CLEAN = [
    DATA / "mission_proposals.json",
    DATA / "repair_proposals.json",
    DATA / "patch_proposals.json",
    DATA / "executive_reviews.json",
    DATA / "missions.json",
    DATA / "memory.json",
    DATA / "lessons_learned.json",
    DATA / "decision_memory.json",
    DATA / "knowledge_queue.json",
    DATA / "deep_code_analysis.json",
]

VOLATILE_KEYS = {
    "id", "uuid", "created", "created_at", "updated", "updated_at",
    "time", "timestamp", "approved", "approved_at", "finished",
    "started", "mission_id", "proposal_id", "review_id",
    "report_path", "archived_at"
}


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


def strip_volatile(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            k: strip_volatile(v)
            for k, v in value.items()
            if k not in VOLATILE_KEYS
        }
    if isinstance(value, list):
        return [strip_volatile(x) for x in value]
    return value


def smart_fingerprint(record: Any) -> str:
    cleaned = strip_volatile(record)

    if isinstance(cleaned, dict):
        strong_parts = {}

        for key in [
            "title", "description", "fix_id", "patch_type", "risk",
            "status", "kind", "goal_title", "action", "summary",
            "next_best_action", "problem", "root_cause", "probable_area"
        ]:
            if key in cleaned:
                strong_parts[key] = cleaned[key]

        if "tasks" in cleaned:
            strong_parts["tasks"] = cleaned["tasks"]

        if "analysis" in cleaned and isinstance(cleaned["analysis"], dict):
            analysis = cleaned["analysis"]
            strong_parts["analysis"] = {
                k: analysis.get(k)
                for k in [
                    "problem", "root_cause", "probable_area",
                    "candidate_files", "keywords"
                ]
                if k in analysis
            }

        if strong_parts:
            return json.dumps(strong_parts, sort_keys=True, ensure_ascii=False)

    return json.dumps(cleaned, sort_keys=True, ensure_ascii=False)


def deduplicate_records(records: list[Any]) -> tuple[list[Any], list[Any]]:
    seen = set()
    kept = []
    removed = []

    for record in records:
        fp = smart_fingerprint(record)
        if fp in seen:
            removed.append(record)
            continue
        seen.add(fp)
        kept.append(record)

    return kept, removed


def clean_json_file(path: Path) -> dict[str, Any]:
    data = load_json(path, None)

    if data is None:
        return {"file": str(path), "status": "missing"}

    if isinstance(data, list):
        kept, removed = deduplicate_records(data)
        if removed:
            archive_path = ARCHIVE / f"dedup_removed_{path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            save_json(archive_path, removed)
            save_json(path, kept)

        return {
            "file": str(path),
            "mode": "list",
            "before": len(data),
            "after": len(kept),
            "removed": len(removed),
        }

    if isinstance(data, dict):
        cleaned_any = False
        result = {
            "file": str(path),
            "mode": "dict",
            "sections": [],
        }

        for key, value in list(data.items()):
            if isinstance(value, list):
                kept, removed = deduplicate_records(value)

                if removed:
                    data[key] = kept
                    cleaned_any = True
                    archive_path = ARCHIVE / f"dedup_removed_{path.stem}_{key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    save_json(archive_path, removed)

                result["sections"].append({
                    "key": key,
                    "before": len(value),
                    "after": len(kept),
                    "removed": len(removed),
                })

        if cleaned_any:
            save_json(path, data)

        return result

    return {"file": str(path), "status": "unsupported_json_type"}


def archive_terminal_missions() -> dict[str, Any]:
    path = DATA / "missions.json"
    missions = load_json(path, [])

    if not isinstance(missions, list):
        return {"file": str(path), "archived": 0, "reason": "not_list"}

    active = []
    archived = []

    for mission in missions:
        if not isinstance(mission, dict):
            active.append(mission)
            continue

        status = str(mission.get("status", "")).lower().strip()
        tasks = mission.get("tasks", [])

        if status in {"completed", "done", "cancelled", "archived"}:
            mission["archived_at"] = now_iso()
            archived.append(mission)
            continue

        if isinstance(tasks, list) and tasks:
            task_statuses = [
                str(t.get("status", "")).lower().strip()
                for t in tasks
                if isinstance(t, dict)
            ]

            if task_statuses and all(s in {"done", "completed"} for s in task_statuses):
                mission["status"] = "completed"
                mission["archived_at"] = now_iso()
                archived.append(mission)
                continue

        active.append(mission)

    if archived:
        archive_path = ARCHIVE / f"missions_lifecycle_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        save_json(archive_path, archived)
        save_json(path, active)

    return {
        "file": str(path),
        "archived": len(archived),
        "remaining_active": len(active),
    }


def enforce_brain_backup_retention() -> dict[str, Any]:
    backup_dir = DATA / "brain_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    backups = [
        item for item in backup_dir.iterdir()
        if item.is_file() and item.name.endswith(".zip")
    ]

    backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    kept = backups[:KEEP_LAST_BRAIN_BACKUPS]
    removed = backups[KEEP_LAST_BRAIN_BACKUPS:]

    for item in removed:
        try:
            item.unlink()
        except Exception:
            pass

    return {
        "backup_dir": str(backup_dir),
        "keep_latest": KEEP_LAST_BRAIN_BACKUPS,
        "found": len(backups),
        "kept": len(kept),
        "removed": len(removed),
    }


def run_smart_garbage_collector() -> dict[str, Any]:
    REPORTS.mkdir(parents=True, exist_ok=True)
    ARCHIVE.mkdir(parents=True, exist_ok=True)

    report = {
        "tool": "Smart Garbage Collector",
        "timestamp": now_iso(),
        "files": [],
        "mission_lifecycle": None,
        "brain_backup_retention": None,
    }

    for path in FILES_TO_CLEAN:
        if path.exists():
            report["files"].append(clean_json_file(path))

    report["mission_lifecycle"] = archive_terminal_missions()
    report["brain_backup_retention"] = enforce_brain_backup_retention()

    report_path = REPORTS / f"smart_garbage_collector_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_json(report_path, report)
    report["report_path"] = str(report_path)

    return report


if __name__ == "__main__":
    print(json.dumps(run_smart_garbage_collector(), indent=2, ensure_ascii=False))
