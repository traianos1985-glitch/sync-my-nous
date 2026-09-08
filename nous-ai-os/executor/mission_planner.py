import json
import os
import time

from executor.goal_system import list_goals, create_goal_mission
from executor.decision_memory import record_decision
from executor.learning_memory import record_lesson

FILE = "data/mission_proposals.json"


def _load():
    if not os.path.exists(FILE):
        return []
    try:
        return json.load(open(FILE, "r", encoding="utf-8"))
    except Exception:
        return []


def _save(items):
    os.makedirs("data", exist_ok=True)
    json.dump(items, open(FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def _goal_kind(goal):
    text = (str(goal.get("title", "")) + " " + str(goal.get("description", ""))).lower()
    if "cloud" in text or "restorable" in text:
        return "cloud"
    if "interface" in text or "dashboard" in text or "ui" in text:
        return "ui"
    if "android" in text or "companion" in text:
        return "android"
    if "autonomy" in text or "approval" in text or "mission" in text:
        return "autonomy"
    return "general"


def _tasks_for_kind(kind):
    if kind == "cloud":
        return [
            {"title": "Check brain backup status", "action": "full_validation"},
            {"title": "Check Vercel deploy status", "action": "vercel_status"},
            {"title": "Check brain readiness", "action": "reality_status"},
            {"title": "Run full validation", "action": "full_validation"},
        ]

    if kind == "ui":
        return [
            {"title": "Check code health", "action": "code_health"},
            {"title": "Check git status", "action": "git_status"},
            {"title": "Run full validation after UI planning", "action": "full_validation"},
        ]

    if kind == "android":
        return [
            {"title": "Check companion status", "action": "companion_status"},
            {"title": "Request UI tree", "action": "companion_ui_tree"},
            {"title": "Run reality check", "action": "reality_status"},
        ]

    if kind == "autonomy":
        return [
            {"title": "Check mission system health", "action": "code_health"},
            {"title": "Check current approvals", "action": "reality_status"},
            {"title": "Run full validation", "action": "full_validation"},
        ]

    return [
        {"title": "Check code health", "action": "code_health"},
        {"title": "Check git status", "action": "git_status"},
        {"title": "Run full validation", "action": "full_validation"},
    ]


def propose_mission_for_goal(goal_id=None):
    goals = list_goals()
    if goal_id:
        candidates = [g for g in goals if str(g.get("id")) == str(goal_id)]
    else:
        candidates = [g for g in goals if g.get("status") == "active"]

    if not candidates:
        return {"ok": False, "error": "goal_not_found_or_no_active_goals"}

    goal = sorted(candidates, key=lambda g: (int(g.get("progress", 0) or 0), int(g.get("priority", 3))))[0]
    kind = _goal_kind(goal)

    title = "Advance goal: " + goal.get("title", "Untitled goal")
    description = "Auto-proposed mission to advance goal progress for: " + goal.get("title", "")

    proposal = {
        "id": int(time.time_ns()),
        "status": "pending",
        "created": time.time(),
        "goal_id": goal.get("id"),
        "goal_title": goal.get("title"),
        "goal_progress": goal.get("progress", 0),
        "kind": kind,
        "title": title,
        "description": description,
        "tasks": _tasks_for_kind(kind),
        "risk": "low",
        "expected_impact": "+5% to +15% goal progress",
        "reason": "Goal is active and can benefit from a safe mission plan.",
    }

    items = _load()

    for existing in items:
        if (
            existing.get("status") == "pending"
            and str(existing.get("goal_id")) == str(goal.get("id"))
            and existing.get("kind") == kind
        ):
            return {"ok": True, "deduped": True, "proposal": existing}

    items.append(proposal)
    _save(items)

    record_decision(
        title="Proposed mission for goal: " + goal.get("title", ""),
        reason=proposal["reason"],
        goal_id=goal.get("id"),
        action="propose_mission",
        result=proposal,
        confidence=0.75,
        tags=["mission_planner", "proposal", kind],
    )

    return {"ok": True, "proposal": proposal}


def list_mission_proposals(limit=50):
    return _load()[-int(limit):]


def mission_planner_status():
    items = _load()
    return {
        "time": time.time(),
        "total": len(items),
        "pending": len([x for x in items if x.get("status") == "pending"]),
        "approved": len([x for x in items if x.get("status") == "approved"]),
        "rejected": len([x for x in items if x.get("status") == "rejected"]),
        "recent": items[-10:],
    }


def _find(items, proposal_id):
    for p in items:
        if str(p.get("id")) == str(proposal_id):
            return p
    return None


def approve_mission_proposal(proposal_id):
    items = _load()
    p = _find(items, proposal_id)
    if not p:
        return {"ok": False, "error": "proposal_not_found"}

    if p.get("status") != "pending":
        return {"ok": False, "error": "proposal_not_pending", "proposal": p}

    created = create_goal_mission(
        p.get("goal_id"),
        p.get("title"),
        p.get("description"),
        p.get("tasks", []),
    )

    p["status"] = "approved"
    p["approved"] = time.time()
    p["mission_id"] = created.get("mission", {}).get("id")

    _save(items)

    decision = record_decision(
        title="Approved mission proposal: " + p.get("title", ""),
        reason="User approved mission proposal.",
        goal_id=p.get("goal_id"),
        mission_id=p.get("mission_id"),
        action="approve_mission_proposal",
        result=created,
        confidence=0.85,
        tags=["mission_planner", "approved", p.get("kind", "general")],
    )

    lesson = record_lesson(
        lesson="Mission proposal approved and converted into mission: " + p.get("title", ""),
        outcome="success",
        goal_id=p.get("goal_id"),
        mission_id=p.get("mission_id"),
        confidence=0.8,
        tags=["mission_planner", "approved", p.get("kind", "general")],
    )

    return {"ok": True, "proposal": p, "created": created, "decision": decision, "lesson": lesson}


def reject_mission_proposal(proposal_id, reason="User rejected mission proposal"):
    items = _load()
    p = _find(items, proposal_id)
    if not p:
        return {"ok": False, "error": "proposal_not_found"}

    p["status"] = "rejected"
    p["rejected"] = time.time()
    p["reject_reason"] = reason
    _save(items)

    decision = record_decision(
        title="Rejected mission proposal: " + p.get("title", ""),
        reason=reason,
        goal_id=p.get("goal_id"),
        action="reject_mission_proposal",
        result=p,
        confidence=0.8,
        tags=["mission_planner", "rejected", p.get("kind", "general")],
    )

    return {"ok": True, "proposal": p, "decision": decision}
