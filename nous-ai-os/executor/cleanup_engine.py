import json
import os
import time
from pathlib import Path

REPORT_FILE = "data/cleanup_reports.json"


def _load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        return json.load(open(path, "r", encoding="utf-8"))
    except Exception:
        return default


def _save_json(path, data):
    os.makedirs(str(Path(path).parent), exist_ok=True)
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def _reports():
    return _load_json(REPORT_FILE, [])


def _save_report(report):
    items = _reports()
    items.append(report)
    items = items[-100:]
    _save_json(REPORT_FILE, items)


def cleanup_status():
    reports = _reports()
    return {
        "time": time.time(),
        "total_reports": len(reports),
        "last_report": reports[-1] if reports else None,
    }


def cleanup_mission_proposals(apply=False):
    path = "data/mission_proposals.json"
    items = _load_json(path, [])
    seen = set()
    changed = []

    for x in items:
        if x.get("status") != "pending":
            continue
        key = (str(x.get("goal_id")), x.get("kind"), x.get("title"))
        if key in seen:
            old = x.get("status")
            if apply:
                x["status"] = "rejected"
                x["reject_reason"] = "Cleanup engine rejected duplicate pending proposal."
                x["rejected"] = time.time()
            changed.append({"id": x.get("id"), "old": old, "new": "rejected", "reason": "duplicate_pending_mission_proposal"})
        else:
            seen.add(key)

    if apply and changed:
        _save_json(path, items)

    return {"ok": True, "file": path, "apply": apply, "changed": changed, "count": len(changed)}


def cleanup_patch_proposals(apply=False):
    path = "data/patch_proposals.json"
    items = _load_json(path, [])
    seen = set()
    changed = []

    for x in items:
        if x.get("status") != "pending":
            continue
        key = (x.get("title"), x.get("risk"), json.dumps(x.get("patches", []), ensure_ascii=False, sort_keys=True))
        if key in seen:
            old = x.get("status")
            if apply:
                x["status"] = "rejected"
                x["reject_reason"] = "Cleanup engine rejected duplicate pending patch proposal."
                x["rejected"] = time.time()
            changed.append({"id": x.get("id"), "old": old, "new": "rejected", "reason": "duplicate_pending_patch_proposal"})
        else:
            seen.add(key)

    if apply and changed:
        _save_json(path, items)

    return {"ok": True, "file": path, "apply": apply, "changed": changed, "count": len(changed)}


def cleanup_repair_proposals(apply=False):
    path = "data/repair_proposals.json"
    items = _load_json(path, [])
    seen = set()
    changed = []

    for x in items:
        if x.get("status") != "pending":
            continue
        key = (x.get("fix_id"), x.get("title"), x.get("description"))
        if key in seen:
            old = x.get("status")
            if apply:
                x["status"] = "rejected"
                x["reject_reason"] = "Cleanup engine rejected duplicate pending repair proposal."
                x["rejected"] = time.time()
            changed.append({"id": x.get("id"), "old": old, "new": "rejected", "reason": "duplicate_pending_repair_proposal"})
        else:
            seen.add(key)

    if apply and changed:
        _save_json(path, items)

    return {"ok": True, "file": path, "apply": apply, "changed": changed, "count": len(changed)}


def cleanup_brain_backups(apply=False, keep=3):
    d = Path("data/brain_backups")
    if not d.exists():
        return {"ok": True, "apply": apply, "changed": [], "count": 0}

    zips = sorted(d.glob("nous_brain_backup_*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    remove = zips[int(keep):]
    changed = []

    for p in remove:
        changed.append({"path": str(p), "reason": "backup_retention_keep_%s" % keep})
        if apply:
            try:
                p.unlink()
            except Exception as e:
                changed[-1]["error"] = str(e)

    return {"ok": True, "apply": apply, "keep": keep, "changed": changed, "count": len(changed)}


def run_cleanup_preview():
    report = {
        "id": int(time.time_ns()),
        "time": time.time(),
        "apply": False,
        "mission_proposals": cleanup_mission_proposals(False),
        "patch_proposals": cleanup_patch_proposals(False),
        "repair_proposals": cleanup_repair_proposals(False),
        "brain_backups": cleanup_brain_backups(False, 3),
    }
    _save_report(report)
    return {"ok": True, "report": report}


def apply_cleanup():
    report = {
        "id": int(time.time_ns()),
        "time": time.time(),
        "apply": True,
        "mission_proposals": cleanup_mission_proposals(True),
        "patch_proposals": cleanup_patch_proposals(True),
        "repair_proposals": cleanup_repair_proposals(True),
        "brain_backups": cleanup_brain_backups(True, 3),
    }
    _save_report(report)
    return {"ok": True, "report": report}


def list_cleanup_reports(limit=20):
    return _reports()[-int(limit):]
