"""Guarded file backup/rollback helpers restricted to the repository workspace."""
import json
import os
import shutil
import tempfile
import time
from pathlib import Path

FILE = "data/rollback_history.json"
BACKUP_DIR = Path("data/patch_file_backups")


def _root():
    return Path.cwd().resolve()


def _load():
    if not os.path.exists(FILE):
        return []
    try:
        with open(FILE, "r", encoding="utf-8") as handle:
            items = json.load(handle)
    except (OSError, ValueError, TypeError):
        return []
    return items if isinstance(items, list) else []


def _save(items):
    target = Path(FILE)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=".rollback_history.", suffix=".tmp", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(items, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, target)
    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def _safe_workspace_path(value, *, must_exist=False):
    if not isinstance(value, (str, os.PathLike)) or not str(value).strip():
        return None
    raw = Path(value)
    candidate = raw if raw.is_absolute() else _root() / raw
    candidate = Path(os.path.abspath(str(candidate)))
    root = _root()
    try:
        relative = candidate.relative_to(root)
    except ValueError:
        return None

    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return None
    if must_exist and not candidate.is_file():
        return None
    if not must_exist and not candidate.parent.is_dir():
        return None
    return candidate


def _safe_backup_path(value):
    if not isinstance(value, (str, os.PathLike)) or not str(value).strip():
        return None
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = _root() / candidate
    candidate = Path(os.path.abspath(str(candidate)))
    base = (_root() / BACKUP_DIR).resolve()
    try:
        candidate.relative_to(base)
    except ValueError:
        return None
    if candidate.is_symlink() or not candidate.is_file():
        return None
    return candidate


def backup_file(path, reason="patch_apply"):
    source = _safe_workspace_path(path, must_exist=True)
    if source is None:
        return {"ok": False, "error": "unsafe_or_missing_source", "path": str(path)}

    backup_dir = _root() / BACKUP_DIR
    backup_dir.mkdir(parents=True, exist_ok=True)
    if backup_dir.is_symlink() or not backup_dir.resolve().is_relative_to(_root()):
        return {"ok": False, "error": "unsafe_backup_directory"}
    backup = backup_dir / (source.name + "." + str(time.time_ns()) + ".bak")
    shutil.copy2(source, backup)

    item = {
        "id": int(time.time_ns()),
        "created": time.time(),
        "type": "file_backup",
        "source": str(source.relative_to(_root())),
        "backup": str(backup.relative_to(_root())),
        "reason": str(reason),
    }
    items = _load()
    items.append(item)
    _save(items)
    return {"ok": True, "backup": item}


def rollback_backup(backup_id):
    items = _load()
    target = next(
        (item for item in items if isinstance(item, dict)
         and str(item.get("id")) == str(backup_id)
         and item.get("type") == "file_backup"),
        None,
    )
    if not target:
        return {"ok": False, "error": "backup_not_found"}

    source = _safe_backup_path(target.get("backup"))
    destination = _safe_workspace_path(target.get("source"), must_exist=False)
    if source is None:
        return {"ok": False, "error": "unsafe_or_missing_backup"}
    if destination is None:
        return {"ok": False, "error": "unsafe_rollback_destination"}

    fd, temp_path = tempfile.mkstemp(prefix=".rollback.", suffix=".tmp", dir=str(destination.parent))
    try:
        with os.fdopen(fd, "wb") as handle, source.open("rb") as backup_handle:
            shutil.copyfileobj(backup_handle, handle)
            handle.flush()
            os.fsync(handle.fileno())
        shutil.copystat(source, temp_path)
        os.replace(temp_path, destination)
    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise

    event = {
        "id": int(time.time_ns()),
        "created": time.time(),
        "type": "rollback",
        "rolled_back_backup_id": backup_id,
        "source": str(destination.relative_to(_root())),
        "backup": str(source.relative_to(_root())),
    }
    items.append(event)
    _save(items)
    return {"ok": True, "rollback": event}


def rollback_status():
    items = _load()
    return {
        "time": time.time(),
        "total": len(items),
        "backups": len([item for item in items if isinstance(item, dict) and item.get("type") == "file_backup"]),
        "rollbacks": len([item for item in items if isinstance(item, dict) and item.get("type") == "rollback"]),
        "recent": items[-20:],
    }


def list_rollbacks(limit=50):
    try:
        limit = max(0, int(limit))
    except (TypeError, ValueError, OverflowError):
        limit = 50
    return _load()[-limit:] if limit else []
