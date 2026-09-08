import json, os, time, subprocess
from pathlib import Path

from executor.rollback_engine import backup_file, rollback_backup

FILE = "data/patch_apply_history.json"

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

def _run(cmd):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return {"ok": p.returncode == 0, "code": p.returncode, "stdout": p.stdout, "stderr": p.stderr}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def patch_apply_status():
    items = _load()
    return {
        "time": time.time(),
        "total": len(items),
        "applied": len([x for x in items if x.get("status") == "applied"]),
        "failed": len([x for x in items if x.get("status") == "failed"]),
        "rolled_back": len([x for x in items if x.get("status") == "rolled_back"]),
        "recent": items[-20:],
    }

def list_patch_apply_history(limit=50):
    return _load()[-int(limit):]

def apply_patch_proposal(proposal_id):
    from executor.patch_generator import list_patch_proposals, approve_patch_proposal

    proposals = list_patch_proposals(500)
    proposal = None

    for p in proposals:
        if str(p.get("id")) == str(proposal_id):
            proposal = p
            break

    if not proposal:
        return {"ok": False, "error": "proposal_not_found"}

    if not proposal.get("can_apply"):
        return {"ok": False, "error": "proposal_cannot_apply"}

    backups = []
    for patch in proposal.get("patches", []):
        path = patch.get("path")
        if path and Path(path).exists():
            b = backup_file(path, reason="patch_apply_proposal_%s" % proposal_id)
            if b.get("ok"):
                backups.append(b["backup"])

    result = approve_patch_proposal(proposal_id)

    validation = {
        "router": _run(["python", "-m", "py_compile", "executor/router.py"]),
        "nous_ui": _run(["python", "-m", "py_compile", "executor/nous_ui.py"]),
    }

    ok = bool(result.get("ok")) and all(x.get("ok") for x in validation.values())

    event = {
        "id": int(time.time_ns()),
        "created": time.time(),
        "proposal_id": proposal_id,
        "status": "applied" if ok else "failed",
        "backups": backups,
        "apply_result": result,
        "validation": validation,
    }

    if not ok:
        rolled = []
        for b in backups:
            rb = rollback_backup(b.get("id"))
            rolled.append(rb)
        event["rollback_after_failure"] = rolled
        event["status"] = "rolled_back"

    items = _load()
    items.append(event)
    _save(items)

    return {"ok": ok, "event": event}
