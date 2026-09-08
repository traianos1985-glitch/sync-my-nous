from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from executor.smart_garbage_collector import run_smart_garbage_collector
from executor.self_maintenance_engine import run_self_maintenance
from executor.patch_proposal_enricher import run_patch_proposal_enricher
from executor.patch_pipeline_manager import run_patch_pipeline_manager
from executor.mission_lifecycle_manager import run_mission_lifecycle_manager
from executor.review_inbox_manager import run_review_inbox_manager
from executor.proposal_creation_guard import run_proposal_creation_guard
from executor.project_health_snapshot import run_project_health_snapshot
from executor.executive_state_summarizer import run_executive_state_summarizer
from executor.executive_prioritizer import run_executive_prioritizer

ROOT = Path.cwd()
DATA = ROOT / "data"
REPORTS = DATA / "reports"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_report(name: str, payload: dict) -> str:
    REPORTS.mkdir(parents=True, exist_ok=True)
    path = REPORTS / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(path)


def run_executive_loop_v4() -> dict:
    smart_cleanup = run_smart_garbage_collector()
    proposal_guard = run_proposal_creation_guard()
    review_inbox = run_review_inbox_manager()
    mission_lifecycle = run_mission_lifecycle_manager()
    basic_maintenance = run_self_maintenance()
    patch_enrichment = run_patch_proposal_enricher()
    patch_pipeline = run_patch_pipeline_manager()
    state_summary = run_executive_state_summarizer()
    health_snapshot = run_project_health_snapshot()
    executive_priorities = run_executive_prioritizer()

    result = {
        "loop": "Executive Loop V4",
        "timestamp": now_iso(),
        "rule": "maintenance_lifecycle_patch_pipeline_before_creation",
        "phase_order": [
            "smart_garbage_collection",
            "proposal_creation_guard",
            "review_inbox_manager",
            "mission_lifecycle_manager",
            "basic_self_maintenance",
            "patch_proposal_enrichment",
            "patch_pipeline_manager",
            "executive_state_summary",
            "project_health_snapshot",
            "executive_prioritizer",
            "safe_observe",
            "safe_recommend"
        ],
        "smart_garbage_collection": smart_cleanup,
        "proposal_creation_guard": proposal_guard,
        "review_inbox_manager": review_inbox,
        "mission_lifecycle_manager": mission_lifecycle,
        "basic_self_maintenance": basic_maintenance,
        "patch_proposal_enrichment": patch_enrichment,
        "patch_pipeline_manager": patch_pipeline,
        "executive_state_summary": state_summary,
        "project_health_snapshot": health_snapshot,
        "executive_prioritizer": executive_priorities,
        "summary": {
            "repository_validation_ok": patch_pipeline.get("repository_validation", {}).get("ok"),
            "health_ok": health_snapshot.get("ok"),
            "patch_proposals_total": patch_pipeline.get("total_patch_proposals"),
            "pending_reviews_total": state_summary.get("pending_reviews", {}).get("total"),
            "active_missions_total": state_summary.get("missions", {}).get("total"),
            "top_priority": executive_priorities.get("top_action"),
            "maintenance_before_creation": True,
            "approval_first": True,
            "rollback_required_on_failed_patch_validation": True,
        },
        "recommendations": [
            "Keep V4 as the main safety gate before new autonomous creation.",
            "Use pending_reviews as the human approval boundary.",
            "Do not apply patches without concrete file changes.",
            "Close mission loops through lifecycle manager and lessons learned.",
            "Continue improving existing modules instead of duplicating architecture.",
        ],
    }

    result["report_path"] = save_report("executive_loop_v4", result)
    return result


if __name__ == "__main__":
    print(json.dumps(run_executive_loop_v4(), indent=2, ensure_ascii=False))
