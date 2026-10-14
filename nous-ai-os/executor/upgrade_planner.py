"""Proposal-only upgrade planner.

Approving a plan records human review intent; it does not generate or execute code.
Implementation must happen through a reviewed source-control change and CI.
"""
import json
import os
import time
from pathlib import Path

FILE = "data/upgrade_plans.json"
_COOLDOWN_DAYS = 30


def _load():
    try:
        with open(FILE, "r", encoding="utf-8") as handle:
            value = json.load(handle)
        if not isinstance(value, list):
            return []
        migrated = False
        for plan in value:
            # Older versions used "implementing" while generating/writing LLM code.
            # On upgrade, downgrade this legacy state to review-only metadata.
            if isinstance(plan, dict) and plan.get("status") == "implementing":
                plan["status"] = "approved"
                plan["execution_mode"] = "proposal_only"
                plan["execution_log"] = list(plan.get("execution_log", [])) + [
                    "Legacy plan migrated to review-only state; automatic execution is disabled."
                ]
                migrated = True
        if migrated:
            _save(value)
        return value
    except (OSError, ValueError, TypeError):
        return []


def _save(items):
    path = Path(FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


UPGRADES = [
    {"title": "True Patch Generator", "priority": 1, "reason": "Turns code analysis into concrete diffs.", "modules": ["deep_code_analyst", "patch_generator", "self_healing_loop"], "file": "executor/true_patch_generator.py"},
    {"title": "Real Code Evolution Engine", "priority": 2, "reason": "Build route/UI/service dependency graph and multi-file patches.", "modules": ["repository_index", "route_graph", "ui_action_graph"], "file": "executor/code_evolution_engine.py"},
    {"title": "Cloud Brain Sync", "priority": 3, "reason": "Protects the brain from device loss.", "modules": ["brain_backup", "cloud_sync", "restore_verify"], "file": "executor/cloud_brain_sync.py"},
    {"title": "Approval Center Actions", "priority": 4, "reason": "Approve/reject directly from Pending Inbox.", "modules": ["pending_review", "approval_router", "ui_buttons"], "file": "executor/approval_center.py"},
]


def propose_upgrade_plan():
    items = _load()
    cutoff = time.time() - _COOLDOWN_DAYS * 86400
    for item in items:
        if item.get("status") == "pending":
            return {"ok": True, "deduped": True, "plan": item}
        if item.get("status") in ("approved", "implemented", "rejected"):
            timestamp = item.get("approved") or item.get("implemented") or item.get("rejected") or item.get("created", 0)
            if timestamp > cutoff:
                return {"ok": True, "deduped": True, "plan": item, "reason": "recent"}

    plan = {
        "id": int(time.time_ns()),
        "created": time.time(),
        "status": "pending",
        "title": "NOUS Next Upgrade Plan",
        "upgrades": [dict(upgrade) for upgrade in UPGRADES],
        "execution_log": ["Πρόταση για ανθρώπινη αξιολόγηση· δεν εκτελείται κώδικας."],
        "execution_mode": "proposal_only",
    }
    items.append(plan)
    _save(items)
    return {"ok": True, "plan": plan}



def propose_release_evidence_plans(limit=5):
    """Create bounded review-only plans from explicitly requested official-release evidence.

    This function is only called by an explicit authenticated API action. It does
    not run during scans, and release-note text is stored as evidence, never as
    instructions or executable input.
    """
    try:
        if isinstance(limit, bool):
            raise ValueError
        count = int(limit)
        if not 1 <= count <= 10:
            raise ValueError
    except (TypeError, ValueError):
        return {"ok": False, "error": "invalid_limit", "allowed_range": [1, 10]}

    # Import locally to keep the general upgrade planner independent at startup.
    from executor.release_triage import triage_latest_releases
    from executor.technical_sources import OFFICIAL_SOURCES

    allowed_sources = {
        source["repository"]: source["url"]
        for source in OFFICIAL_SOURCES
        if isinstance(source, dict)
        and isinstance(source.get("repository"), str)
        and isinstance(source.get("url"), str)
    }
    queue = triage_latest_releases(limit=25)
    queue_status = queue.get("status", "not_scanned")
    if queue_status not in {"complete", "partial"}:
        # A successful HTTP/API call is not a successful proposal run when
        # upstream evidence was never retrieved. Keep the reason machine-readable.
        return {
            "ok": False,
            "error": "release_evidence_unavailable",
            "created_count": 0,
            "deduped_count": 0,
            "plans": [],
            "deduped_plans": [],
            "source_queue_status": queue_status,
            "safety": {
                "triggered_explicitly": True,
                "release_text_executed": False,
                "code_generated": False,
                "code_executed": False,
                "source_files_modified": 0,
                "dependency_changes_performed": 0,
                "requires_human_review": True,
            },
        }
    candidates = [
        item for item in queue.get("items", [])
        if isinstance(item, dict)
        and item.get("action") == "review_only"
        and item.get("status") == "needs_human_review"
        and isinstance(item.get("signals"), list)
        and any(signal in {"security", "breaking_change", "bug_fix", "performance"}
                for signal in item["signals"])
    ]

    items = _load()
    created = []
    deduped = []
    deduped_keys = set()
    for evidence in candidates:
        repository = evidence.get("repository")
        tag = evidence.get("tag")
        source_url = evidence.get("source_url")
        if not all(isinstance(value, str) and value.strip()
                   for value in (repository, tag, source_url)):
            continue
        allowed_url = allowed_sources.get(repository)
        if not allowed_url or not (
            source_url == allowed_url or source_url.startswith(allowed_url + "/")
        ):
            continue
        # Recheck the allowlist here as a defence-in-depth boundary.
        existing = next((
            plan for plan in items
            if isinstance(plan, dict)
            and isinstance(plan.get("source_evidence"), dict)
            and plan["source_evidence"].get("repository") == repository
            and plan["source_evidence"].get("tag") == tag
        ), None)
        if existing:
            evidence_key = (repository, tag)
            if evidence_key not in deduped_keys:
                deduped.append(existing)
                deduped_keys.add(evidence_key)
            continue
        plan = {
            "id": int(time.time_ns()),
            "created": time.time(),
            "status": "pending",
            "title": f"Review upstream release: {evidence.get('project') or repository} {tag}",
            "plan_type": "release_evidence_review",
            "source_evidence": {
                "project": str(evidence.get("project") or "")[:80],
                "repository": repository[:120],
                "release": str(evidence.get("release") or tag)[:180],
                "tag": tag[:100],
                "published_at": str(evidence.get("published_at") or "")[:40],
                "source_url": source_url[:300],
                "excerpt": str(evidence.get("evidence_excerpt") or "")[:700],
                "signals": [signal for signal in evidence["signals"]
                            if signal in {"security", "breaking_change", "bug_fix", "performance"}],
                "confidence": evidence.get("confidence", "unclassified"),
                "notes_are_untrusted_data": True,
            },
            "upgrades": [{
                "title": f"Evaluate {repository} {tag}",
                "priority": 1 if evidence.get("priority") == "high" else 2,
                "reason": "Official release-note signals require human verification; compatibility and relevance are not established.",
                "modules": [],
                "file": None,
            }],
            "review_checklist": [
                "Verify whether this upstream project is actually used by the repository or deployed runtime.",
                "Read the complete official release notes and any linked security advisory.",
                "Check supported versions, breaking changes, and compatibility with the current manifests and runtime.",
                "Run focused tests and the full CI suite before proposing any implementation.",
                "If relevant, implement separately in a reviewed pull request; do not apply changes from this proposal.",
            ],
            "execution_log": [
                "Created only after an explicit request to draft proposals from release evidence.",
                "Release-note content is untrusted reference data and was not executed.",
                "Πρόταση για ανθρώπινη αξιολόγηση· δεν εκτελείται κώδικας.",
            ],
            "execution_mode": "proposal_only",
            "code_generated": False,
            "code_executed": False,
        }
        items.append(plan)
        created.append(plan)
        if len(created) >= count:
            break

    if created:
        _save(items)
    return {
        "ok": True,
        "created_count": len(created),
        "deduped_count": len(deduped),
        "plans": created,
        "deduped_plans": deduped[:count],
        "source_queue_status": queue_status,
        "safety": {
            "triggered_explicitly": True,
            "release_text_executed": False,
            "code_generated": False,
            "code_executed": False,
            "source_files_modified": 0,
            "dependency_changes_performed": 0,
            "requires_human_review": True,
        },
    }


def upgrade_planner_status():
    items = _load()
    return {
        "time": time.time(),
        "total": len(items),
        "pending": sum(item.get("status") == "pending" for item in items),
        "approved_for_review": sum(item.get("status") == "approved" for item in items),
        "plans": items[-20:],
        "execution_enabled": False,
    }


def list_upgrade_plans(limit=20):
    try:
        count = max(1, min(int(limit), 100))
    except (TypeError, ValueError):
        count = 20
    return _load()[-count:]


def approve_upgrade_plan(plan_id):
    """Mark a pending proposal as approved for review, never as executable."""
    items = _load()
    for plan in items:
        if str(plan.get("id")) == str(plan_id):
            if plan.get("status") != "pending":
                return {"ok": False, "error": "plan_not_pending", "plan": plan}
            plan["status"] = "approved"
            plan["approved"] = time.time()
            plan["execution_mode"] = "proposal_only"
            plan["execution_log"] = list(plan.get("execution_log", [])) + [
                "✅ Εγκρίθηκε για τεχνική αξιολόγηση. Δεν δημιουργήθηκε ούτε εκτελέστηκε κώδικας.",
                "Επόμενο βήμα: ξεχωριστό reviewed PR με tests και επιτυχές CI.",
            ]
            _save(items)
            return {
                "ok": True,
                "approved_for_review": True,
                "code_generated": False,
                "code_executed": False,
                "plan": plan,
            }
    return {"ok": False, "error": "plan_not_found"}


def get_plan(plan_id: str) -> dict | None:
    for plan in _load():
        if str(plan.get("id")) == str(plan_id):
            return plan
    return None


def reject_upgrade_plan(plan_id, reason="User rejected upgrade plan"):
    items = _load()
    for plan in items:
        if str(plan.get("id")) == str(plan_id):
            if plan.get("status") != "pending":
                return {"ok": False, "error": "plan_not_pending", "plan": plan}
            plan["status"] = "rejected"
            plan["rejected"] = time.time()
            plan["reject_reason"] = str(reason)[:500]
            _save(items)
            return {"ok": True, "plan": plan}
    return {"ok": False, "error": "plan_not_found"}
