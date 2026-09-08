from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.cwd()
DATA = ROOT / "data"
REPORTS = DATA / "reports"
PRIORITIES = DATA / "executive_priorities.json"


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


def score_item(kind: str, item: dict[str, Any]) -> dict[str, Any]:
    status = str(item.get("status", "")).lower()
    title = str(item.get("title", "Untitled"))

    impact = 40
    urgency = 20
    risk_penalty = 0
    dependency = 10

    text = json.dumps(item, ensure_ascii=False).lower()

    if kind == "patch_review":
        impact += 30
        urgency += 25
        dependency += 15

    if kind == "pending_review":
        impact += 25
        urgency += 20

    if kind == "mission":
        impact += 20
        urgency += 10

    if "auth" in text or "unauthorized" in text or "401" in text:
        impact += 20
        urgency += 20

    if "blocked" in status or "blocked" in text:
        urgency += 20

    if "pending" in status:
        urgency += 10

    if "low" in text:
        risk_penalty += 0
    elif "medium" in text:
        risk_penalty += 10
    elif "high" in text:
        risk_penalty += 25

    priority = max(0, min(100, impact + urgency + dependency - risk_penalty))

    return {
        "priority": priority,
        "kind": kind,
        "title": title,
        "status": item.get("status"),
        "id": item.get("id") or item.get("proposal_id") or item.get("mission_id"),
        "impact": impact,
        "urgency": urgency,
        "dependency": dependency,
        "risk_penalty": risk_penalty,
        "recommended_action": item.get("recommended_action") or infer_action(kind, item),
    }


def infer_action(kind: str, item: dict[str, Any]) -> str:
    if kind == "patch_review":
        return "Review patch proposal before applying."
    if kind == "pending_review":
        return "Open pending review and decide approve/reject."
    if kind == "mission":
        return "Inspect blocked/running mission and unblock next safe task."
    if kind == "mission_proposal":
        return "Review mission proposal."
    return "Review item."


def collect_items() -> list[dict[str, Any]]:
    items = []

    for p in load_json(DATA / "patch_proposals.json", []):
        if isinstance(p, dict):
            items.append(score_item("patch_review", p))

    for r in load_json(DATA / "pending_reviews.json", []):
        if isinstance(r, dict):
            items.append(score_item("pending_review", r))

    for m in load_json(DATA / "missions.json", []):
        if isinstance(m, dict):
            items.append(score_item("mission", m))

    for mp in load_json(DATA / "mission_proposals.json", []):
        if isinstance(mp, dict):
            items.append(score_item("mission_proposal", mp))

    items.sort(key=lambda x: x.get("priority", 0), reverse=True)
    return items


def run_executive_prioritizer() -> dict[str, Any]:
    REPORTS.mkdir(parents=True, exist_ok=True)

    items = collect_items()
    report = {
        "tool": "Executive Prioritizer",
        "timestamp": now_iso(),
        "total_items_scored": len(items),
        "top_10": items[:10],
        "top_action": items[0] if items else None,
    }

    save_json(PRIORITIES, report)

    report_path = REPORTS / f"executive_prioritizer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_json(report_path, report)
    report["report_path"] = str(report_path)
    return report


if __name__ == "__main__":
    print(json.dumps(run_executive_prioritizer(), indent=2, ensure_ascii=False))
