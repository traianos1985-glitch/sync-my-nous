import difflib
import json
import os
import time

from executor.self_diagnosis import run_self_diagnosis

FILE = "data/repair_proposals.json"


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


def repair_status():
    items = _load()
    return {
        "time": time.time(),
        "total": len(items),
        "pending": len([x for x in items if x.get("status") == "pending"]),
        "approved": len([x for x in items if x.get("status") == "approved"]),
        "rejected": len([x for x in items if x.get("status") == "rejected"]),
        "recent": items[-10:],
    }


def list_repair_proposals(limit=50):
    return _load()[-int(limit):]


def _make_diff(path, old, new):
    return "".join(difflib.unified_diff(
        old.splitlines(True),
        new.splitlines(True),
        fromfile=path + ".before",
        tofile=path + ".after",
    ))


def propose_repair_from_diagnosis():
    diagnosis = run_self_diagnosis()
    proposals = []

    for fix in diagnosis.get("recommended_fixes", []):
        if fix.get("id") == "dashboard_auth_helpers":
            proposals.append({
                "id": int(time.time_ns()),
                "status": "pending",
                "created": time.time(),
                "fix_id": "dashboard_auth_helpers",
                "title": fix.get("title"),
                "description": fix.get("description"),
                "risk": fix.get("risk", "low"),
                "target_files": ["executor/nous_ui.py"],
                "patch_type": "safe_known_fix",
                "diff": "Known safe fix will reinstall central dashboard auth/error helpers.",
                "diagnosis_ok": diagnosis.get("ok"),
            })

    if not proposals and diagnosis.get("ok"):
        proposals.append({
            "id": int(time.time_ns()),
            "status": "pending",
            "created": time.time(),
            "fix_id": "no_action_needed",
            "title": "No repair needed",
            "description": "Self diagnosis reports no problems. No code patch is needed.",
            "risk": "none",
            "target_files": [],
            "patch_type": "noop",
            "diff": "",
            "diagnosis_ok": True,
        })

    items = _load()
    items.extend(proposals)
    _save(items)

    return {
        "ok": True,
        "diagnosis_ok": diagnosis.get("ok"),
        "created": proposals,
        "count": len(proposals),
        "diagnosis": diagnosis,
    }


def _find(items, proposal_id):
    for p in items:
        if str(p.get("id")) == str(proposal_id):
            return p
    return None


def approve_repair_proposal(proposal_id):
    items = _load()
    p = _find(items, proposal_id)
    if not p:
        return {"ok": False, "error": "proposal_not_found"}

    if p.get("status") != "pending":
        return {"ok": False, "error": "proposal_not_pending", "proposal": p}

    if p.get("fix_id") == "no_action_needed":
        p["status"] = "approved"
        p["approved"] = time.time()
        _save(items)
        return {"ok": True, "proposal": p, "message": "No repair was needed."}

    if p.get("fix_id") == "dashboard_auth_helpers":
        from executor.self_diagnosis import apply_safe_self_fix
        result = apply_safe_self_fix("dashboard_auth_helpers")
        p["status"] = "approved" if result.get("ok") else "failed"
        p["approved"] = time.time()
        p["result"] = result
        _save(items)
        return {"ok": result.get("ok"), "proposal": p, "result": result}

    return {"ok": False, "error": "unknown_or_unsafe_fix", "proposal": p}


def reject_repair_proposal(proposal_id, reason="User rejected repair proposal"):
    items = _load()
    p = _find(items, proposal_id)
    if not p:
        return {"ok": False, "error": "proposal_not_found"}

    p["status"] = "rejected"
    p["rejected"] = time.time()
    p["reject_reason"] = reason
    _save(items)

    return {"ok": True, "proposal": p}
