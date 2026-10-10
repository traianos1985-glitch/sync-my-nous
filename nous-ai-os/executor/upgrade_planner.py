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
        return value if isinstance(value, list) else []
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
