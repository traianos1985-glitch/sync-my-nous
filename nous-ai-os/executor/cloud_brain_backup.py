import json
import os
import time
import hashlib
import zipfile

from executor.brain_state import save_brain_state

BACKUP_DIR = "data/brain_backups"

FILES = [
    "data/brain_state.json",
    "data/goals_v2.json",
    "data/missions.json",
    "data/memory.json",
    "data/knowledge_base.json",
    "data/knowledge_queue.json",
    "data/vercel_deployments.json",
]


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def create_brain_backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)

    save_brain_state()

    ts = int(time.time())
    out = f"{BACKUP_DIR}/nous_brain_backup_{ts}.zip"

    manifest = {
        "created": time.time(),
        "type": "NOUS_BRAIN_BACKUP",
        "version": 1,
        "files": [],
    }

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for path in FILES:
            if os.path.exists(path):
                z.write(path, path)
                manifest["files"].append({
                    "path": path,
                    "sha256": _sha256(path),
                    "size": os.path.getsize(path),
                })

        z.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

    return {
        "ok": True,
        "backup": out,
        "manifest": manifest,
        "size": os.path.getsize(out),
    }


def list_brain_backups():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    items = []

    for name in sorted(os.listdir(BACKUP_DIR), reverse=True):
        if not name.endswith(".zip"):
            continue
        path = f"{BACKUP_DIR}/{name}"
        items.append({
            "name": name,
            "path": path,
            "size": os.path.getsize(path),
            "created": os.path.getmtime(path),
            "sha256": _sha256(path),
        })

    return {
        "ok": True,
        "count": len(items),
        "backups": items,
        "time": time.time(),
    }


def brain_backup_status():
    return {
        "time": time.time(),
        "backup_dir": BACKUP_DIR,
        "tracked_files": FILES,
        "existing": list_brain_backups(),
    }
