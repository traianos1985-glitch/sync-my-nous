import subprocess
import time
from pathlib import Path

from executor.rollback_engine import backup_file, rollback_backup
from executor.json_state_store import read_list, write_list

FILE = "data/patch_apply_history.json"


def _load():
    return read_list(FILE)


def _save(items):
    write_list(FILE, items)


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
            backup = backup_file(path, reason="patch_apply_proposal_%s" % proposal_id)
            if backup.get("ok"):
                backups.append(backup["backup"])

    result = approve_patch_proposal(proposal_id)
    proposal_status = (result.get("proposal") or {}).get("status")
    applied_paths = (
        ((result.get("proposal") or {}).get("result") or {}).get("applied", [])
        if result.get("ok") else []
    )

    validation = {}
    if result.get("ok") and applied_paths:
        for path in sorted(set(applied_paths)):
            if path.endswith(".py"):
                validation[path] = _run(["python", "-m", "py_compile", path])

    ok = bool(result.get("ok")) and bool(applied_paths) and all(
        check.get("ok") for check in validation.values()
    )
    event = {
        "id": int(time.time_ns()),
        "created": time.time(),
        "proposal_id": proposal_id,
        "status": (
            "applied" if ok else
            "not_applied" if result.get("error") == "proposal_not_pending" else
            proposal_status or "failed"
        ),
        "backups": backups,
        "apply_result": result,
        "validation": validation,
        "verification": "syntax_only" if ok else "not_verified",
        "persistence": "runtime_filesystem_only" if ok else "none",
    }

    # Roll back only when a real write occurred and subsequent validation failed.
    if applied_paths and not ok:
        rolled_back = []
        for backup in backups:
            rollback_result = rollback_backup(backup.get("id"))
            rolled_back.append(rollback_result)
        event["rollback_after_failure"] = rolled_back
        event["status"] = "rolled_back"

    items = _load()
    items.append(event)
    _save(items)

    return {"ok": ok, "event": event}
