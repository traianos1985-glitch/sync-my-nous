from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.cwd()
DATA = ROOT / "data"
REPORTS = DATA / "reports"
PENDING_REVIEWS = DATA / "pending_reviews.json"


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
    return json.dumps(reduced, sort_keys=True, ensure_ascii=False)


def run_review_inbox_manager() -> dict[str, Any]:
    REPORTS.mkdir(parents=True, exist_ok=True)

    reviews = load_json(PENDING_REVIEWS, [])
    if not isinstance(reviews, list):
        reviews = []

    seen = set()
    kept = []
    removed = 0

    for review in reviews:
        fp = fingerprint(review)
        if fp in seen:
            removed += 1
            continue
        seen.add(fp)

        if isinstance(review, dict):
            review.setdefault("status", "pending")
            review.setdefault("created_at", now_iso())

        kept.append(review)

    if removed:
        save_json(PENDING_REVIEWS, kept)

    by_kind = {}
    for review in kept:
        if isinstance(review, dict):
            kind = str(review.get("kind", "unknown"))
            by_kind[kind] = by_kind.get(kind, 0) + 1

    report = {
        "tool": "Review Inbox Manager",
        "timestamp": now_iso(),
        "before": len(reviews),
        "after": len(kept),
        "removed_duplicates": removed,
        "by_kind": by_kind,
    }

    report_path = REPORTS / f"review_inbox_manager_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_json(report_path, report)
    report["report_path"] = str(report_path)
    return report


if __name__ == "__main__":
    print(json.dumps(run_review_inbox_manager(), indent=2, ensure_ascii=False))
