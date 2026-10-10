import hashlib
import json
import os
import tempfile
import time
import zipfile
from pathlib import Path

from executor.brain_state import save_brain_state

BACKUP_DIR = "data/brain_backups"
DATA_ROOT = Path("data")

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
EXCLUDED_NAMES = {
    ".env", ".env.local", ".env.production",
    "api_tokens.json", "secrets.json", "credentials.json",
}
EXCLUDED_DIR_NAMES = {
    "brain_backups",
    "brain_restores",
    "__pycache__",
    ".cache",
}
MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_BACKUP_BYTES = 256 * 1024 * 1024


def _is_excluded(path: str) -> bool:
    parts = Path(path).parts
    if path in EXCLUDED_FILES or Path(path).name in EXCLUDED_NAMES:
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
    found.update(path for path in FILES if os.path.isfile(path) and not os.path.islink(path) and not _is_excluded(path))
    return sorted(found)


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _fsync_directory(directory):
    try:
        fd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError:
        pass


def create_brain_backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    temp_path = None
    try:
        save_brain_state()
        stamp = time.time_ns()
        out = os.path.join(BACKUP_DIR, f"nous_brain_backup_{stamp}.zip")
        fd, temp_path = tempfile.mkstemp(prefix=".nous-backup-", suffix=".tmp", dir=BACKUP_DIR)
        os.close(fd)
        manifest = {
            "created": time.time(),
            "type": "NOUS_BRAIN_BACKUP",
            "version": 2,
            "files": [],
        }
        total_size = 0
        with zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in _runtime_files():
                try:
                    with open(path, "rb") as source:
                        data = source.read(MAX_FILE_BYTES + 1)
                except OSError:
                    continue
                size = len(data)
                if size > MAX_FILE_BYTES or total_size + size > MAX_BACKUP_BYTES:
                    continue
                digest = hashlib.sha256(data).hexdigest()
                archive.writestr(path, data)
                total_size += size
                manifest["files"].append({"path": path, "sha256": digest, "size": size})
            archive.writestr("manifest.json", json.dumps(
                manifest, ensure_ascii=False, indent=2, allow_nan=False
            ))

        with zipfile.ZipFile(temp_path, "r") as archive:
            bad_member = archive.testzip()
            if bad_member is not None:
                raise RuntimeError(f"backup_archive_verification_failed:{bad_member}")
        with open(temp_path, "rb") as handle:
            os.fsync(handle.fileno())
        os.replace(temp_path, out)
        temp_path = None
        _fsync_directory(BACKUP_DIR)
        return {
            "ok": True,
            "backup": out,
            "manifest": manifest,
            "size": os.path.getsize(out),
            "sha256": _sha256(out),
            "verified": True,
        }
    except Exception as exc:
        return {"ok": False, "error": "backup_creation_failed", "details": str(exc)}
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError:
                pass


def list_brain_backups():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    items = []
    for name in sorted(os.listdir(BACKUP_DIR), reverse=True):
        if not name.endswith(".zip"):
            continue
        path = os.path.join(BACKUP_DIR, name)
        if os.path.islink(path) or not os.path.isfile(path):
            continue
        try:
            items.append({
                "name": name,
                "path": path,
                "size": os.path.getsize(path),
                "created": os.path.getmtime(path),
                "sha256": _sha256(path),
            })
        except OSError:
            continue
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
        "existing": list_brain_backups(),
    }
