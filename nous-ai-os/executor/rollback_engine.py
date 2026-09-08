import json, os, time, shutil
from pathlib import Path

FILE = "data/rollback_history.json"
BACKUP_DIR = Path("data/patch_file_backups")

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

def backup_file(path, reason="patch_apply"):
    p = Path(path)
    if not p.exists():
        return {"ok": False, "error": "file_not_found", "path": path}

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup = BACKUP_DIR / (p.name + "." + str(int(time.time_ns())) + ".bak")
    shutil.copy2(p, backup)

    item = {
        "id": int(time.time_ns()),
        "created": time.time(),
        "type": "file_backup",
        "source": str(p),
        "backup": str(backup),
        "reason": reason,
    }

    items = _load()
    items.append(item)
    _save(items)

    return {"ok": True, "backup": item}

def rollback_backup(backup_id):
    items = _load()
    target = None

    for x in items:
        if str(x.get("id")) == str(backup_id):
            target = x
            break

    if not target:
        return {"ok": False, "error": "backup_not_found"}

    src = Path(target["backup"])
    dst = Path(target["source"])

    if not src.exists():
        return {"ok": False, "error": "backup_file_missing", "backup": str(src)}

    shutil.copy2(src, dst)

    event = {
        "id": int(time.time_ns()),
        "created": time.time(),
        "type": "rollback",
        "rolled_back_backup_id": backup_id,
        "source": str(dst),
        "backup": str(src),
    }

    items.append(event)
    _save(items)

    return {"ok": True, "rollback": event}

def rollback_status():
    items = _load()
    return {
        "time": time.time(),
        "total": len(items),
        "backups": len([x for x in items if x.get("type") == "file_backup"]),
        "rollbacks": len([x for x in items if x.get("type") == "rollback"]),
        "recent": items[-20:],
    }

def list_rollbacks(limit=50):
    return _load()[-int(limit):]
