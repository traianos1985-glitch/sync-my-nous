from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.cwd()
DATA = ROOT / "data"
REPORTS = DATA / "reports"

PATCH_PROPOSALS = DATA / "patch_proposals.json"
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


def has_real_patch(proposal: dict[str, Any]) -> bool:
    if isinstance(proposal.get("diff"), str) and proposal["diff"].strip():
        return True
    if isinstance(proposal.get("patch"), str) and proposal["patch"].strip():
        return True
    if isinstance(proposal.get("files"), list) and proposal["files"]:
        return True
    if isinstance(proposal.get("patches"), list) and proposal["patches"]:
        return True
    return False


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


def build_patch_draft(proposal: dict[str, Any]) -> dict[str, Any]:
    analysis = proposal.get("analysis", {})
    if not isinstance(analysis, dict):
        analysis = {}

    return {
        "created_at": now_iso(),
        "source": "patch_proposal_enricher",
        "problem": analysis.get("problem"),
        "root_cause": analysis.get("root_cause"),
        "probable_area": analysis.get("probable_area"),
        "candidate_files": analysis.get("candidate_files", []),
        "keywords": analysis.get("keywords", []),
        "draft_status": "needs_concrete_diff",
        "proposed_next_step": "Use existing executor.patch_generator.generate_patch_from_analysis to create patches list and diff.",
    }


def try_existing_patch_generator(analysis: dict[str, Any]) -> dict[str, Any]:
    try:
        from executor.patch_generator import generate_patch_from_analysis
    except Exception as e:
        return {
            "ok": False,
            "error": "patch_generator_import_failed",
            "detail": repr(e),
        }

    try:
        generated = generate_patch_from_analysis(analysis)
    except Exception as e:
        return {
            "ok": False,
            "error": "patch_generation_failed",
            "detail": repr(e),
        }

    if not isinstance(generated, dict):
        return {
            "ok": False,
            "error": "patch_generator_returned_non_dict",
            "type": str(type(generated)),
        }

    return {
        "ok": bool(generated.get("ok")),
        "generated": generated,
    }


def enrich_one(proposal: dict[str, Any]) -> dict[str, Any]:
    analysis = proposal.get("analysis", {})
    if not isinstance(analysis, dict):
        analysis = {}

    before_has_patch = has_real_patch(proposal)

    result = {
        "proposal_id": proposal.get("id"),
        "title": proposal.get("title"),
        "status": proposal.get("status"),
        "before_has_patch": before_has_patch,
        "after_has_patch": before_has_patch,
        "actions": [],
        "generator": None,
    }

    proposal.setdefault("patch_draft", build_patch_draft(proposal))

    if before_has_patch:
        proposal["can_apply"] = bool(proposal.get("can_apply", True))
        proposal["patch_draft"]["draft_status"] = "concrete_patch_available"
        result["actions"].append("already_has_patch")
        result["after_has_patch"] = True
        return result

    if analysis:
        generated = try_existing_patch_generator(analysis)
        result["generator"] = generated

        if generated.get("ok") and isinstance(generated.get("generated"), dict):
            g = generated["generated"]

            if isinstance(g.get("patches"), list) and g["patches"]:
                proposal["patches"] = g["patches"]
                proposal["can_apply"] = bool(g.get("can_apply", True))
                proposal["patch_draft"]["draft_status"] = "concrete_patch_available"
                proposal["patch_draft"]["generated_at"] = now_iso()
                proposal["patch_draft"]["generated_by"] = "executor.patch_generator.generate_patch_from_analysis"
                result["actions"].append("attached_generated_patches")

            if isinstance(g.get("diff"), str) and g["diff"].strip():
                proposal["diff"] = g["diff"]
                result["actions"].append("attached_generated_diff")

            if isinstance(g.get("risk"), str):
                proposal["risk"] = g["risk"]

            if isinstance(g.get("title"), str) and g["title"].strip():
                proposal.setdefault("generated_title", g["title"])

    after_has_patch = has_real_patch(proposal)
    result["after_has_patch"] = after_has_patch

    if after_has_patch:
        proposal["can_apply"] = bool(proposal.get("can_apply", True))
        add_pending_review({
            "kind": "patch_ready_for_review",
            "status": "pending",
            "created_at": now_iso(),
            "proposal_id": proposal.get("id"),
            "title": "Patch ready for review",
            "summary": {
                "proposal_id": proposal.get("id"),
                "title": proposal.get("title"),
                "risk": proposal.get("risk"),
                "candidate_files": analysis.get("candidate_files", []),
                "has_patches": isinstance(proposal.get("patches"), list) and bool(proposal.get("patches")),
                "has_diff": isinstance(proposal.get("diff"), str) and bool(proposal.get("diff").strip()),
            },
            "recommended_action": "Review generated patch before approval/apply.",
        })
    else:
        proposal["can_apply"] = False
        add_pending_review({
            "kind": "patch_needs_concrete_diff",
            "status": "pending",
            "created_at": now_iso(),
            "proposal_id": proposal.get("id"),
            "title": "Patch needs concrete diff",
            "summary": proposal.get("patch_draft"),
            "recommended_action": "Patch proposal has analysis but no concrete file changes yet.",
        })

    if not result["actions"]:
        result["actions"].append("created_patch_draft_only")

    return result

def run_patch_proposal_enricher() -> dict[str, Any]:
    REPORTS.mkdir(parents=True, exist_ok=True)

    proposals = load_json(PATCH_PROPOSALS, [])
    if not isinstance(proposals, list):
        proposals = []

    report = {
        "tool": "Patch Proposal Enricher",
        "timestamp": now_iso(),
        "total": len(proposals),
        "results": [],
    }

    changed = False

    for proposal in proposals:
        if not isinstance(proposal, dict):
            continue

        before = json.dumps(proposal, sort_keys=True, ensure_ascii=False)
        result = enrich_one(proposal)
        after = json.dumps(proposal, sort_keys=True, ensure_ascii=False)

        if before != after:
            changed = True

        report["results"].append(result)

    if changed:
        save_json(PATCH_PROPOSALS, proposals)

    report_path = REPORTS / f"patch_proposal_enricher_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_json(report_path, report)
    report["report_path"] = str(report_path)

    return report


if __name__ == "__main__":
    print(json.dumps(run_patch_proposal_enricher(), indent=2, ensure_ascii=False))
