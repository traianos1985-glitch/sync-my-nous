from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.cwd()
DATA = ROOT / "data"
REPORTS = DATA / "reports"
SUMMARY = DATA / "executive_state_summary.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def count_status(items: Any) -> dict[str, int]:
    result = {}
    if not isinstance(items, list):
        return result
    for item in items:
        if isinstance(item, dict):
            status = str(item.get("status", "unknown"))
            result[status] = result.get(status, 0) + 1
    return result


def run_executive_state_summarizer() -> dict[str, Any]:
    REPORTS.mkdir(parents=True, exist_ok=True)

    missions = load_json(DATA / "missions.json", [])
    mission_proposals = load_json(DATA / "mission_proposals.json", [])
    repair_proposals = load_json(DATA / "repair_proposals.json", [])
    patch_proposals = load_json(DATA / "patch_proposals.json", [])
    pending_reviews = load_json(DATA / "pending_reviews.json", [])

    summary = {
        "tool": "Executive State Summarizer",
        "timestamp": now_iso(),
        "missions": {
            "total": len(missions) if isinstance(missions, list) else 0,
            "by_status": count_status(missions),
        },
        "mission_proposals": {
            "total": len(mission_proposals) if isinstance(mission_proposals, list) else 0,
            "by_status": count_status(mission_proposals),
        },
        "repair_proposals": {
            "total": len(repair_proposals) if isinstance(repair_proposals, list) else 0,
            "by_status": count_status(repair_proposals),
        },
        "patch_proposals": {
            "total": len(patch_proposals) if isinstance(patch_proposals, list) else 0,
            "by_status": count_status(patch_proposals),
            "ready_with_patch": len([
                p for p in patch_proposals
                if isinstance(p, dict) and (
                    p.get("diff") or p.get("patch") or p.get("patches") or p.get("files")
                )
            ]) if isinstance(patch_proposals, list) else 0,
        },
        "pending_reviews": {
            "total": len(pending_reviews) if isinstance(pending_reviews, list) else 0,
            "by_status": count_status(pending_reviews),
        },
        "next_focus": [
            "Use lifecycle manager to close completed missions.",
            "Use patch pipeline only after approval.",
            "Keep cleanup before creation.",
        ],
    }

    SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path = REPORTS / f"executive_state_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    summary["report_path"] = str(report_path)
    return summary


if __name__ == "__main__":
    print(json.dumps(run_executive_state_summarizer(), indent=2, ensure_ascii=False))
