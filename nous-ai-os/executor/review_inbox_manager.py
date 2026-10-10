from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from executor.json_state_store import edit_list

ROOT = Path.cwd()
DATA = ROOT / "data"
REPORTS = DATA / "reports"
PENDING_REVIEWS = DATA / "pending_reviews.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    """Read a JSON file without hiding corruption of the review queue."""
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError) as exc:
        raise RuntimeError(f"review_inbox_integrity_failure:{path}") from exc


def save_json(path: Path, data: Any) -> None:
    """Persist a report atomically so readers never see a partial JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=".review-report-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False, allow_nan=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
        try:
            dir_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except OSError:
            pass
    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def fingerprint(item: Any) -> str:
    if not isinstance(item, dict):
        return json.dumps(item, sort_keys=True, ensure_ascii=False)
    reduced = {
        "kind": item.get("kind"),
        "proposal_id": item.get("proposal_id"),
        "mission_id": item.get("mission_id"),
        "title": item.get("title"),
        "recommended_action": item.get("recommended_action"),
    }
    return json.dumps(reduced, sort_keys=True, ensure_ascii=False, allow_nan=False)


def run_review_inbox_manager() -> dict[str, Any]:
    REPORTS.mkdir(parents=True, exist_ok=True)

    # Keep de-duplication and persistence inside the same cross-process lock.
    with edit_list(str(PENDING_REVIEWS)) as stored:
        before = len(stored)
        seen = set()
        kept = []
        removed = 0

        for review in stored:
            fp = fingerprint(review)
            if fp in seen:
                removed += 1
                continue
            seen.add(fp)
            review.setdefault("status", "pending")
            review.setdefault("created_at", now_iso())
            kept.append(review)

        stored[:] = kept

    by_kind = {}
    for review in kept:
        kind = str(review.get("kind", "unknown"))
        by_kind[kind] = by_kind.get(kind, 0) + 1

    report = {
        "tool": "Review Inbox Manager",
        "timestamp": now_iso(),
        "before": before,
        "after": len(kept),
        "removed_duplicates": removed,
        "by_kind": by_kind,
    }

    report_path = REPORTS / f"review_inbox_manager_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
    save_json(report_path, report)
    report["report_path"] = str(report_path)
    return report


if __name__ == "__main__":
    print(json.dumps(run_review_inbox_manager(), indent=2, ensure_ascii=False))
