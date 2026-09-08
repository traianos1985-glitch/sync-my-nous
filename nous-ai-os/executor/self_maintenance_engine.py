from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.cwd()
DATA = ROOT / "data"
REPORTS = DATA / "reports"
ARCHIVE = DATA / "archive"
BACKUPS = DATA / "backups"

JSON_TARGETS = [
    DATA / "pending_reviews.json",
    DATA / "mission_proposals.json",
    DATA / "repair_proposals.json",
    DATA / "patch_proposals.json",
    DATA / "missions.json",
    DATA / "goals.json",
]

BACKUP_KEEP_LATEST = 10


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


def normalize_record(record: Any) -> str:
    if isinstance(record, dict):
        clone = {
            k: v for k, v in record.items()
            if k not in {
                "id", "created_at", "updated_at", "timestamp",
                "review_id", "proposal_id", "uuid"
            }
        }
        return json.dumps(clone, sort_keys=True, ensure_ascii=False)
    return json.dumps(record, sort_keys=True, ensure_ascii=False)


def deduplicate_list(items: list[Any]) -> tuple[list[Any], int]:
    seen = set()
    result = []
    removed = 0

    for item in items:
        key = normalize_record(item)
        if key in seen:
            removed += 1
            continue
        seen.add(key)
        result.append(item)

    return result, removed


def cleanup_json_file(path: Path) -> dict[str, Any]:
    original = load_json(path, [])

    if isinstance(original, dict):
        for key in ["items", "reviews", "proposals", "missions", "goals"]:
            if isinstance(original.get(key), list):
                cleaned, removed = deduplicate_list(original[key])
                original[key] = cleaned
                save_json(path, original)
                return {
                    "file": str(path),
                    "mode": f"dict.{key}",
                    "removed_duplicates": removed,
                    "remaining": len(cleaned),
                }

        return {
            "file": str(path),
            "mode": "dict",
            "removed_duplicates": 0,
            "remaining": len(original),
        }

    if isinstance(original, list):
        cleaned, removed = deduplicate_list(original)
        save_json(path, cleaned)
        return {
            "file": str(path),
            "mode": "list",
            "removed_duplicates": removed,
            "remaining": len(cleaned),
        }

    return {
        "file": str(path),
        "mode": "unknown",
        "removed_duplicates": 0,
        "remaining": 0,
    }


def archive_completed_or_stale_missions() -> dict[str, Any]:
    path = DATA / "missions.json"
    missions = load_json(path, [])

    if not isinstance(missions, list):
        return {"file": str(path), "archived": 0, "reason": "missions.json not list"}

    active = []
    archived = []

    for mission in missions:
        if not isinstance(mission, dict):
            active.append(mission)
            continue

        status = str(mission.get("status", "")).lower()
        if status in {"completed", "done", "cancelled", "archived"}:
            mission["archived_at"] = now_iso()
            archived.append(mission)
        else:
            active.append(mission)

    if archived:
        archive_file = ARCHIVE / f"missions_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        save_json(archive_file, archived)
        save_json(path, active)

    return {
        "file": str(path),
        "archived": len(archived),
        "remaining_active": len(active),
    }


def enforce_backup_retention() -> dict[str, Any]:
    BACKUPS.mkdir(parents=True, exist_ok=True)

    candidates = []
    for item in BACKUPS.iterdir():
        if item.is_file() or item.is_dir():
            candidates.append(item)

    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    kept = candidates[:BACKUP_KEEP_LATEST]
    removed = candidates[BACKUP_KEEP_LATEST:]

    for item in removed:
        try:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        except Exception:
            pass

    return {
        "backup_dir": str(BACKUPS),
        "keep_latest": BACKUP_KEEP_LATEST,
        "kept": len(kept),
        "removed": len(removed),
    }


def run_self_maintenance() -> dict[str, Any]:
    REPORTS.mkdir(parents=True, exist_ok=True)
    ARCHIVE.mkdir(parents=True, exist_ok=True)

    results = {
        "timestamp": now_iso(),
        "deduplication": [],
        "mission_lifecycle": None,
        "backup_retention": None,
    }

    for path in JSON_TARGETS:
        if path.exists():
            results["deduplication"].append(cleanup_json_file(path))

    results["mission_lifecycle"] = archive_completed_or_stale_missions()
    results["backup_retention"] = enforce_backup_retention()

    report_path = REPORTS / f"self_maintenance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_json(report_path, results)
    results["report_path"] = str(report_path)

    return results


if __name__ == "__main__":
    result = run_self_maintenance()
    print(json.dumps(result, indent=2, ensure_ascii=False))
