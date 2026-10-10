import hashlib
import json
import os
import time
import zipfile
from pathlib import Path

from executor.brain_state import save_brain_state

BACKUP_DIR = "data/brain_backups"
DATA_ROOT = Path("data")

# Explicit core files are kept for clarity; runtime discovery also captures new state.
FILES = [
    "data/brain_state.json",
    "data/goals_v2.json",
    "data/missions.json",
    "data/memory.json",
    "data/knowledge_base.json",
    "data/knowledge_queue.json",
    "data/vercel_deployments.json",
]
EXCLUDED_FILES = {
    "data/api_tokens.json",
    "data/secrets.json",
    "data/credentials.json",
}
EXCLUDED_NAMES = {".env", ".env.local", ".env.production"}
EXCLUDED_DIR_NAMES = {
    "brain_backups",
    "brain_restores",
    "__pycache__",
    ".cache",
}
MAX_FILE_BYTES = 64 * 1024 * 1024


def _is_excluded(path: str) -> bool:
    parts = Path(path).parts
    if path in EXCLUDED_FILES:
        return True
    if any(part in EXCLUDED_DIR_NAMES for part in parts):
        return True
    if Path(path).name in EXCLUDED_NAMES:
        return True
    return False


def _runtime_files():
    """Discover regular runtime files below data/, excluding secrets and archives."""
    found = set()
    if DATA_ROOT.exists():
        for root, dirs, files in os.walk(DATA_ROOT, followlinks=False):
            dirs[:] = sorted(
                name for name in dirs
                if name not in EXCLUDED_DIR_NAMES
                and not os.path.islink(os.path.join(root, name))
            )
            for name in files:
                path = os.path.join(root, name).replace(os.sep, "/")
                if _is_excluded(path) or os.path.islink(path) or not os.path.isfile(path):
                    continue
                try:
                    if os.path.getsize(path) > MAX_FILE_BYTES:
                        continue
                except OSError:
                    continue
                found.add(path)
    found.update(path for path in FILES if os.path.isfile(path) and not _is_excluded(path))
    return sorted(found)


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
        "version": 2,
        "files": [],
    }

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in _runtime_files():
            try:
                size = os.path.getsize(path)
                digest = _sha256(path)
                archive.write(path, path)
            except OSError:
                # Runtime files may be updated or removed while a backup is running.
                continue
            manifest["files"].append({"path": path, "sha256": digest, "size": size})
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

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
        if os.path.islink(path) or not os.path.isfile(path):
            continue
        items.append({
            "name": name,
            "path": path,
            "size": os.path.getsize(path),
            "created": os.path.getmtime(path),
            "sha256": _sha256(path),
        })
    return {"ok": True, "count": len(items), "backups": items, "time": time.time()}


def brain_backup_status():
    files = _runtime_files()
    return {
        "time": time.time(),
        "backup_dir": BACKUP_DIR,
        "tracked_files": files,
        "excluded_files": sorted(EXCLUDED_FILES),
        "backup_scope": (
            "Regular runtime files under data/ including JSON, uploads and generated apps; "
            "excludes token/credential files, symlinks, caches and backup/restore archives"
        ),
        "skipped_oversized_files": [],
        "existing": list_brain_backups(),
    }
