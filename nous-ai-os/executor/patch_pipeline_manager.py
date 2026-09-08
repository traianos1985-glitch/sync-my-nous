from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.cwd()
DATA = ROOT / "data"
REPORTS = DATA / "reports"

PATCH_PROPOSALS = DATA / "patch_proposals.json"
PENDING_REVIEWS = DATA / "pending_reviews.json"

SAFE_PIPELINE_STATES = {
    "pending": "proposal_created",
    "approved": "approved_waiting_for_apply",
    "applied": "patch_applied",
    "validated": "validation_passed",
    "failed": "validation_failed",
    "rolled_back": "rollback_executed",
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


def run_cmd(cmd: list[str]) -> dict[str, Any]:
    try:
        p = subprocess.run(
            cmd,
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            timeout=60,
        )
        return {
            "ok": p.returncode == 0,
            "code": p.returncode,
            "stdout": p.stdout[-4000:],
            "stderr": p.stderr[-4000:],
        }
    except Exception as e:
        return {
            "ok": False,
            "code": -1,
            "stdout": "",
            "stderr": repr(e),
        }


def proposal_has_diff(proposal: dict[str, Any]) -> bool:
    diff = proposal.get("diff")
    if isinstance(diff, str) and diff.strip():
        return True

    patch = proposal.get("patch")
    if isinstance(patch, str) and patch.strip():
        return True

    files = proposal.get("files")
    if isinstance(files, list) and files:
        return True

    patches = proposal.get("patches")
    if isinstance(patches, list) and patches:
        return True

    return False


def proposal_summary(proposal: dict[str, Any]) -> dict[str, Any]:
    analysis = proposal.get("analysis", {})
    if not isinstance(analysis, dict):
        analysis = {}

    return {
        "id": proposal.get("id"),
        "title": proposal.get("title"),
        "status": proposal.get("status"),
        "risk": proposal.get("risk"),
        "has_diff": proposal_has_diff(proposal),
        "root_cause": analysis.get("root_cause") or proposal.get("root_cause"),
        "probable_area": analysis.get("probable_area") or proposal.get("probable_area"),
        "candidate_files": analysis.get("candidate_files") or proposal.get("candidate_files"),
    }


def validate_repository() -> dict[str, Any]:
    checks = {
        "compile_patch_pipeline_manager": run_cmd([
            "python", "-m", "py_compile",
            "executor/patch_pipeline_manager.py"
        ]),
        "compile_existing_core": run_cmd([
            "python", "-m", "py_compile",
            "executor/smart_garbage_collector.py",
            "executor/self_maintenance_engine.py",
            "executor/executive_loop_v4.py",
        ]),
        "git_status": run_cmd(["git", "status", "--short"]),
    }
    checks["ok"] = all(
        item.get("ok", False)
        for key, item in checks.items()
        if isinstance(item, dict) and key != "git_status"
    )
    return checks


def add_pending_review(review: dict[str, Any]) -> None:
    reviews = load_json(PENDING_REVIEWS, [])
    if not isinstance(reviews, list):
        reviews = []

    key = json.dumps({
        "kind": review.get("kind"),
        "proposal_id": review.get("proposal_id"),
        "title": review.get("title"),
    }, sort_keys=True, ensure_ascii=False)

    for existing in reviews:
        if not isinstance(existing, dict):
            continue
        existing_key = json.dumps({
            "kind": existing.get("kind"),
            "proposal_id": existing.get("proposal_id"),
            "title": existing.get("title"),
        }, sort_keys=True, ensure_ascii=False)
        if existing_key == key:
            return

    reviews.append(review)
    save_json(PENDING_REVIEWS, reviews)


def process_patch_proposal(proposal: dict[str, Any]) -> dict[str, Any]:
    status = str(proposal.get("status", "pending")).lower().strip()
    has_diff = proposal_has_diff(proposal)

    pipeline = proposal.setdefault("pipeline", {})
    pipeline["last_checked"] = now_iso()
    pipeline["state"] = SAFE_PIPELINE_STATES.get(status, "unknown")

    result = {
        "proposal": proposal_summary(proposal),
        "pipeline_state": pipeline["state"],
        "actions": [],
        "blocked": False,
        "reason": None,
    }

    if status == "pending":
        result["actions"].append("waiting_for_user_approval")
        add_pending_review({
            "kind": "patch_proposal",
            "status": "pending",
            "created_at": now_iso(),
            "proposal_id": proposal.get("id"),
            "title": proposal.get("title", "Patch proposal"),
            "summary": proposal_summary(proposal),
            "recommended_action": "Review patch proposal before apply.",
        })
        return result

    if status == "approved" and not has_diff:
        result["blocked"] = True
        result["reason"] = "approved_patch_has_no_diff_or_file_changes"
        result["actions"].append("blocked_before_apply")
        pipeline["state"] = "blocked_missing_diff"
        pipeline["blocked_reason"] = result["reason"]

        add_pending_review({
            "kind": "patch_pipeline_blocker",
            "status": "pending",
            "created_at": now_iso(),
            "proposal_id": proposal.get("id"),
            "title": "Patch pipeline blocked: missing diff",
            "summary": proposal_summary(proposal),
            "recommended_action": "Generate concrete diff before applying patch.",
        })
        return result

    if status == "approved" and has_diff:
        result["actions"].append("approved_but_apply_requires_existing_patch_apply_engine")
        pipeline["state"] = "approved_ready_for_apply_engine"
        return result

    if status in {"applied", "validated", "failed", "rolled_back"}:
        validation = validate_repository()
        pipeline["validation"] = validation
        result["validation"] = validation
        result["actions"].append("validated_repository_state")
        return result

    result["actions"].append("no_action_for_status")
    return result


def run_patch_pipeline_manager() -> dict[str, Any]:
    REPORTS.mkdir(parents=True, exist_ok=True)

    proposals = load_json(PATCH_PROPOSALS, [])
    if not isinstance(proposals, list):
        proposals = []

    report = {
        "tool": "Patch Pipeline Manager",
        "timestamp": now_iso(),
        "policy": "approval_first_no_diff_no_apply",
        "total_patch_proposals": len(proposals),
        "results": [],
        "repository_validation": validate_repository(),
    }

    changed = False

    for proposal in proposals:
        if not isinstance(proposal, dict):
            continue

        before = json.dumps(proposal, sort_keys=True, ensure_ascii=False)
        result = process_patch_proposal(proposal)
        after = json.dumps(proposal, sort_keys=True, ensure_ascii=False)

        if before != after:
            changed = True

        report["results"].append(result)

    if changed:
        save_json(PATCH_PROPOSALS, proposals)

    report_path = REPORTS / f"patch_pipeline_manager_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_json(report_path, report)
    report["report_path"] = str(report_path)

    return report

if __name__ == "__main__":
    print(json.dumps(run_patch_pipeline_manager(), indent=2, ensure_ascii=False))
