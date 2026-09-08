from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.cwd()
DATA = ROOT / "data"
REPORTS = DATA / "reports"

TARGETS = [
    DATA / "mission_proposals.json",
    DATA / "repair_proposals.json",
    DATA / "patch_proposals.json",
    DATA / "pending_reviews.json",
]

VOLATILE = {
    "id", "created", "created_at", "updated", "updated_at",
    "time", "timestamp", "approved", "approved_at",
    "mission_id", "proposal_id", "review_id",
}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def clean(value: Any):
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items() if k not in VOLATILE}
    if isinstance(value, list):
        return [clean(x) for x in value]
    return value


def fingerprint(item: Any) -> str:
    if isinstance(item, dict):
        core = {}
        for k in [
            "kind", "title", "description", "fix_id", "patch_type",
            "risk", "goal_title", "root_cause", "probable_area",
            "recommended_action"
        ]:
            if k in item:
                core[k] = item[k]

        if "analysis" in item and isinstance(item["analysis"], dict):
            a = item["analysis"]
            core["analysis"] = {
                "problem": a.get("problem"),
                "root_cause": a.get("root_cause"),
                "probable_area": a.get("probable_area"),
                "candidate_files": a.get("candidate_files"),
            }

        if core:
            return json.dumps(clean(core), sort_keys=True, ensure_ascii=False)

    return json.dumps(clean(item), sort_keys=True, ensure_ascii=False)


def guard_file(path: Path) -> dict[str, Any]:
    items = load_json(path, [])
    if not isinstance(items, list):
        return {"file": str(path), "status": "not_list"}

    seen = set()
    kept = []
    blocked = []

    for item in items:
        fp = fingerprint(item)
        if fp in seen:
            blocked.append(item)
            continue
        seen.add(fp)
        kept.append(item)

    if blocked:
        save_json(path, kept)

    return {
        "file": str(path),
        "before": len(items),
        "after": len(kept),
        "duplicates_blocked": len(blocked),
    }


def run_proposal_creation_guard() -> dict[str, Any]:
    REPORTS.mkdir(parents=True, exist_ok=True)

    report = {
        "tool": "Proposal Creation Guard",
        "timestamp": now_iso(),
        "policy": "block_duplicate_proposals_and_reviews",
        "results": [],
    }

    for path in TARGETS:
        if path.exists():
            report["results"].append(guard_file(path))

    report_path = REPORTS / f"proposal_creation_guard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_json(report_path, report)
    report["report_path"] = str(report_path)
    return report


if __name__ == "__main__":
    print(json.dumps(run_proposal_creation_guard(), indent=2, ensure_ascii=False))
